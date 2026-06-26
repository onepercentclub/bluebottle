from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from django.test.client import RequestFactory
from django.utils.timezone import now

from bluebottle.geo.models import GeoFeature
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory, GeolocationFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.serializers import DateActivitySerializer
from bluebottle.time_based.tests.factories import DateActivityFactory, DateActivitySlotFactory, \
    DateParticipantFactory


class DateActivitySerializerTestCase(BluebottleTestCase):
    def setUp(self):
        self.activity = DateActivityFactory.create(slots=[])

        self.serializer = DateActivitySerializer()
        self.request_factory = RequestFactory()

    def assertAttribute(self, attr, value, params=None, user=None):
        request = self.request_factory.get('/', params or None)
        request.user = user or AnonymousUser()
        request.query_params = {}
        serializer = DateActivitySerializer(context={'request': request})
        data = serializer.to_representation(instance=self.activity)

        self.assertEqual(data[attr], value)

    def test_date_info_no_slots(self):
        self.assertAttribute('date_info', {
            'capacity': None,
            'count': 0,
            'first': None,
            'end': None,
            'is_full': True,
            'duration': None,
            'has_multiple': False,
            'spots_left': None,
            'total': 0
        })

    def test_date_info_single_slot(self):
        slot = DateActivitySlotFactory.create(activity=self.activity)
        self.assertAttribute('date_info', {
            'capacity': 10,
            'count': 1,
            'first': slot.start,
            'end': slot.end,
            'duration': timedelta(hours=2),
            'is_full': False,
            'has_multiple': False,
            'spots_left': 10,
            'total': 1
        })

    def test_date_info_multiple_dates(self):
        slots = [
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=2)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=4)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=6)),
        ]

        self.assertAttribute('date_info', {
            'capacity': 30,
            'count': 3,
            'first': min(slot.start.date() for slot in slots),
            'end': max(slot.end.date() for slot in slots),
            'duration': None,
            'is_full': False,
            'has_multiple': True,
            'spots_left': 30,
            'total': 3
        })

    def test_date_info_multiple_dates_full(self):
        slots = [
            DateActivitySlotFactory.create(
                activity=self.activity, start=now() + timedelta(days=2), status='full'
            ),
            DateActivitySlotFactory.create(
                activity=self.activity, start=now() + timedelta(days=4), status='full'
            ),
            DateActivitySlotFactory.create(
                activity=self.activity, start=now() + timedelta(days=6), status='full'
            ),
        ]

        self.assertAttribute('date_info', {
            'capacity': 30,
            'count': 3,
            'first': min(slot.start.date() for slot in slots),
            'end': max(slot.end.date() for slot in slots),
            'duration': None,
            'is_full': True,
            'has_multiple': True,
            'spots_left': 30,
            'total': 3
        })

    def test_date_info_multiple_dates_overlapping(self):
        slots = [
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=2)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=2)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=6)),
        ]

        self.assertAttribute('date_info', {
            'capacity': 30,
            'count': 3,
            'first': min(slot.start.date() for slot in slots),
            'end': max(slot.end.date() for slot in slots),
            'duration': None,
            'is_full': False,
            'has_multiple': True,
            'spots_left': 30,
            'total': 3
        })

    def test_date_info_multiple_dates_filtered(self):
        slots = [
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=2)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=4)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=6)),
        ]

        self.assertAttribute(
            'date_info',
            {
                'capacity': 20,
                'count': 2,
                'duration': None,
                'is_full': False,
                'first': min(slot.start.date() for slot in slots),
                'end': max(slot.end.date() for slot in slots),
                'has_multiple': True,
                'spots_left': 20,
                'total': 2
            },
            {
                'filter[start]': (now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'filter[end]': (now() + timedelta(days=4)).strftime('%Y-%m-%d')
            }

        )

    def test_location_info_no_slots(self):
        self.assertAttribute(
            'location_info',
            {
                'is_online': False,
                'has_multiple': False,
                'location': None,
                'online_meeting_url': None,
                'location_hint': None,
            }
        )

    def test_location_info_single_slot(self):
        slot = DateActivitySlotFactory.create(activity=self.activity)
        self.assertAttribute(
            'location_info',
            {
                'has_multiple': False,
                'is_online': False,
                'location': {
                    'locality': slot.location.locality,
                    'formattedAddress': slot.location.formatted_address,
                    'country': {
                        'code': slot.location.country.alpha2_code
                    }
                },
                'online_meeting_url': None,
                'location_hint': None,
            }
        )

    def test_location_info_all_online(self):
        DateActivitySlotFactory.create_batch(
            3,
            activity=self.activity, is_online=True,
            location=None, online_meeting_url='http://meet.up'
        )

        self.assertAttribute(
            'location_info',
            {
                'has_multiple': False,
                'is_online': True,
                'location': None,
                'online_meeting_url': None,
                'location_hint': None,
            }
        )

    def test_location_info_all_online_participant(self):
        DateActivitySlotFactory.create_batch(
            3,
            activity=self.activity, is_online=True,
            location=None, online_meeting_url='http://meet.up'
        )

        user = BlueBottleUserFactory.create()
        DateParticipantFactory.create(
            user=user, activity=self.activity, status='accepted', slot=self.activity.slots.first()
        )

        self.assertAttribute(
            'location_info',
            {
                'has_multiple': False,
                'is_online': True,
                'location': None,
                'online_meeting_url': 'http://meet.up',
                'location_hint': None,
            },
            user=user
        )

    def test_location_info_multiple_locations(self):
        DateActivitySlotFactory.create(activity=self.activity)
        DateActivitySlotFactory.create(activity=self.activity)
        DateActivitySlotFactory.create(activity=self.activity)

        self.assertAttribute(
            'location_info',
            {
                'has_multiple': True,
                'is_online': False,
                'location': None,
                'online_meeting_url': None,
                'location_hint': None,
            }
        )

    def _attach_geofeatures(self, geolocation, address_name, shared_features):
        address = GeoFeature.objects.create(
            mapbox_id='address-{}'.format(geolocation.pk),
            feature_type='address',
        )
        address.set_current_language('en')
        address.name = address_name
        address.place_name = address_name
        address.save()

        geolocation.geofeatures.set([address] + list(shared_features))
        geolocation.geofeature = address
        geolocation.save(skip_mapbox_sync=True)

    def test_location_info_multiple_locations_same_place(self):
        country = CountryFactory.create(alpha2_code='NL')
        shared_place = GeoFeature.objects.create(
            mapbox_id='place-amsterdam',
            feature_type='place',
        )
        shared_place.set_current_language('en')
        shared_place.name = 'Amsterdam'
        shared_place.place_name = 'Amsterdam, Netherlands'
        shared_place.save()

        shared_country = GeoFeature.objects.create(
            mapbox_id='country-nl',
            feature_type='country',
        )
        shared_country.set_current_language('en')
        shared_country.name = 'Netherlands'
        shared_country.place_name = 'Netherlands'
        shared_country.save()

        location_one = GeolocationFactory.create(locality='Street 1', country=country)
        location_two = GeolocationFactory.create(locality='Street 2', country=country)
        self._attach_geofeatures(location_one, 'Street 1', [shared_place, shared_country])
        self._attach_geofeatures(location_two, 'Street 2', [shared_place, shared_country])

        DateActivitySlotFactory.create(activity=self.activity, location=location_one)
        DateActivitySlotFactory.create(activity=self.activity, location=location_two)

        self.assertAttribute(
            'location_info',
            {
                'has_multiple': True,
                'is_online': False,
                'location': {
                    'locality': 'Amsterdam',
                    'formattedAddress': 'Amsterdam, Netherlands',
                    'country': {
                        'code': 'NL',
                    },
                },
                'online_meeting_url': None,
                'location_hint': None,
            }
        )

    def test_location_info_multiple_locations_same_neighborhood(self):
        country = CountryFactory.create(alpha2_code='NL')
        shared_neighborhood = GeoFeature.objects.create(
            mapbox_id='neighborhood-groenoord',
            feature_type='neighborhood',
        )
        shared_neighborhood.set_current_language('en')
        shared_neighborhood.name = 'Groenoord'
        shared_neighborhood.place_name = 'Groenoord, Leiden, The Netherlands'
        shared_neighborhood.save()

        shared_place = GeoFeature.objects.create(
            mapbox_id='place-leiden',
            feature_type='place',
        )
        shared_place.set_current_language('en')
        shared_place.name = 'Leiden'
        shared_place.place_name = 'Leiden, The Netherlands'
        shared_place.save()

        shared_country = GeoFeature.objects.create(
            mapbox_id='country-nl',
            feature_type='country',
        )
        shared_country.set_current_language('en')
        shared_country.name = 'Netherlands'
        shared_country.place_name = 'Netherlands'
        shared_country.save()

        location_one = GeolocationFactory.create(locality='Street 1', country=country)
        location_two = GeolocationFactory.create(locality='Street 2', country=country)
        shared = [shared_neighborhood, shared_place, shared_country]
        self._attach_geofeatures(location_one, 'Street 1', shared)
        self._attach_geofeatures(location_two, 'Street 2', shared)

        DateActivitySlotFactory.create(activity=self.activity, location=location_one)
        DateActivitySlotFactory.create(activity=self.activity, location=location_two)

        self.assertAttribute(
            'location_info',
            {
                'has_multiple': True,
                'is_online': False,
                'location': {
                    'locality': 'Groenoord',
                    'formattedAddress': 'Groenoord, Leiden, The Netherlands',
                    'country': {
                        'code': 'NL',
                    },
                },
                'online_meeting_url': None,
                'location_hint': None,
            }
        )

    def test_location_info_multiple_slots_single_location(self):
        location = GeolocationFactory.create()

        DateActivitySlotFactory.create(activity=self.activity, location=location)
        DateActivitySlotFactory.create(activity=self.activity, location=location)
        DateActivitySlotFactory.create(
            activity=self.activity,
            location=location,
            location_hint='test hint'
        )

        self.assertAttribute(
            'location_info',
            {
                'has_multiple': False,
                'is_online': False,
                'location': {
                    'locality': location.locality,
                    'formattedAddress': location.formatted_address,
                    'country': {
                        'code': location.country.alpha2_code
                    }
                },
                'online_meeting_url': None,
                'location_hint': None,
            }
        )

    def test_location_info_multiple_dates_filtered(self):
        slots = [
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=2)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=4)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=6)),
        ]

        location = slots[0].location
        self.assertAttribute(
            'location_info',
            {
                'has_multiple': False,
                'is_online': False,
                'location': {
                    'locality': location.locality,
                    'formattedAddress': location.formatted_address,
                    'country': {
                        'code': location.country.alpha2_code
                    }
                },
                'online_meeting_url': None,
                'location_hint': None,
            },
            {
                'filter[start]': (now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'filter[end]': (now() + timedelta(days=3)).strftime('%Y-%m-%d')
            }
        )
