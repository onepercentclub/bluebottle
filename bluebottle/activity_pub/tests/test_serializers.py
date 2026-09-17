from decimal import Decimal
from io import BytesIO

import mock
from django.contrib.gis.geos import Point
from django.test import RequestFactory
from django.test.utils import override_settings
from djmoney.money import Money
from requests import Response

from bluebottle.activity_links.serializers import LinkedLocationSerializer
from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import GoodDeed, CrowdFunding, GrantApplication
from bluebottle.activity_pub.serializers.federated_activities import (
    FederatedDateActivitySerializer,
    FederatedFundingSerializer,
    LocationSerializer,
)
from bluebottle.activity_pub.serializers.json_ld import (
    DoGoodEventSerializer, GoodDeedSerializer, CrowdFundingSerializer, GrantApplicationSerializer
)
from bluebottle.activity_pub.tests.factories import (
    DoGoodEventFactory
)
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.geo.models import GeoFeature, Geolocation
from bluebottle.geo.tests.mapbox_fixtures import MAPBOX_V6_ADDRESS_FEATURE
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory, GeolocationFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import DateActivityFactory, DateActivitySlotFactory


class DoGoodEventSerializerTestCase(BluebottleTestCase):
    activity_pub_serializer = DoGoodEventSerializer
    federated_serializer = FederatedDateActivitySerializer
    factory = DateActivityFactory
    activity_pub_factory = DoGoodEventFactory

    def setUp(self):
        self.settings = SitePlatformSettings.objects.create(
            share_activities=['supplier', 'consumer']
        )
        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as image_file:
            self.mock_image_response = Response()
            self.mock_image_response.raw = BytesIO(image_file.read())
            self.mock_image_response.status_code = 200

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()

        return {'request': request}

    def test_to_json_ld(self):
        model = self.factory.create()
        federated_serializer = self.federated_serializer(
            instance=model,
            context=self.context
        )

        activity_pub_serializer = self.activity_pub_serializer(
            data=federated_serializer.data,
            context=self.context
        )

        self.assertTrue(activity_pub_serializer.is_valid(raise_exception=True))

        do_good_event = activity_pub_serializer.save()

        self.assertEqual(do_good_event.name, model.title)
        self.assertEqual(do_good_event.summary, model.description.html)
        self.assertEqual(do_good_event.sub_event.count(), model.slots.count())

    def test_to_json_ld_slots_keep_individual_locations(self):
        model = self.factory.create(slots=[])
        first_location = GeolocationFactory.create()
        second_location = GeolocationFactory.create()
        DateActivitySlotFactory.create(activity=model, location=first_location)
        DateActivitySlotFactory.create(activity=model, location=second_location)

        federated_serializer = self.federated_serializer(
            instance=model,
            context=self.context
        )

        activity_pub_serializer = self.activity_pub_serializer(
            data=federated_serializer.data,
            context=self.context
        )

        self.assertTrue(activity_pub_serializer.is_valid(raise_exception=True))
        do_good_event = activity_pub_serializer.save()

        serialized_locations = {
            (
                slot.location.latitude,
                slot.location.longitude
            )
            for slot in do_good_event.sub_event.all()
        }
        expected_locations = {
            (first_location.position.x, first_location.position.y),
            (second_location.position.x, second_location.position.y),
        }
        self.assertSetEqual(serialized_locations, expected_locations)

    def test_to_json_ld_already_exists(self):
        model = self.factory.create()
        federated_serializer = self.federated_serializer(
            instance=model,
            context=self.context
        )

        activity_pub_serializer = self.activity_pub_serializer(
            data=federated_serializer.data,
            context=self.context
        )

        self.assertTrue(activity_pub_serializer.is_valid(raise_exception=True))

        do_good_event = activity_pub_serializer.save()

        self.activity_pub_serializer(instance=do_good_event, data=federated_serializer.data, context=self.context)
        self.assertTrue(activity_pub_serializer.is_valid(raise_exception=True))
        do_good_event = activity_pub_serializer.save()

        self.assertEqual(do_good_event.name, model.title)
        self.assertEqual(do_good_event.summary, model.description.html)
        self.assertEqual(do_good_event.sub_event.count(), model.slots.count())

    def test_to_federated_activity(self):
        activity_pub_model = self.activity_pub_factory.create(iri='http://example.com')

        federated_serializer = self.activity_pub_serializer(
            instance=activity_pub_model, context=self.context
        )
        serializer = self.federated_serializer(
            data=federated_serializer.data, context=self.context
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))

        with mock.patch('requests.get', return_value=self.mock_image_response):
            activity = serializer.save()

        self.assertEqual(activity.title, activity_pub_model.name)
        self.assertEqual(activity.description.html, activity_pub_model.summary)
        self.assertEqual(activity.slots.count(), activity_pub_model.sub_event.count())

    def test_to_federated_activity_already_exists(self):
        activity_pub_model = self.activity_pub_factory.create(iri='http://example.com')

        federated_serializer = self.activity_pub_serializer(
            instance=activity_pub_model, context=self.context
        )

        serializer = self.federated_serializer(
            data=federated_serializer.data, context=self.context
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))

        with mock.patch('requests.get', return_value=self.mock_image_response):
            activity = serializer.save()

        serializer = self.federated_serializer(
            instance=activity, data=federated_serializer.data, context=self.context
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))

        with mock.patch('requests.get', return_value=self.mock_image_response):
            activity = serializer.save()

        self.assertEqual(activity.title, activity_pub_model.name)
        self.assertEqual(activity.description.html, activity_pub_model.summary)
        self.assertEqual(activity.slots.count(), activity_pub_model.sub_event.count())

    def test_url_field_included_when_set(self):
        """Test that url field is included in serialized output when it's set."""
        do_good_event = self.activity_pub_factory.create(
            url='https://example.com/activity'
        )
        serializer = self.activity_pub_serializer(
            instance=do_good_event, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertEqual(data['url'], 'https://example.com/activity')

    def test_url_field_included_when_none(self):
        """Test that url field is included in serialized output even when it's None."""
        do_good_event = self.activity_pub_factory.create(url=None)
        serializer = self.activity_pub_serializer(
            instance=do_good_event, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertIsNone(data['url'])


class FederatedFundingSerializerTestCase(BluebottleTestCase):
    def setUp(self):
        SitePlatformSettings.objects.create(
            share_activities=['supplier', 'consumer']
        )

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()
        return {'request': request}

    def test_donated_includes_matching_amount(self):
        funding = FundingFactory.create(
            target=Money(1000, 'EUR'),
            amount_donated=Money(90, 'EUR'),
            amount_matching=Money(30, 'EUR'),
        )

        data = FederatedFundingSerializer(instance=funding, context=self.context).data

        self.assertEqual(Decimal(data['donated']), Decimal('120.00'))
        self.assertEqual(data['donated_currency'], 'EUR')

    def test_donated_includes_matching_amount_in_activity_pub_payload(self):
        funding = FundingFactory.create(
            target=Money(1000, 'EUR'),
            amount_donated=Money(90, 'EUR'),
            amount_matching=Money(30, 'EUR'),
        )

        federated_data = FederatedFundingSerializer(
            instance=funding,
            context=self.context,
        ).data
        activity_pub_serializer = CrowdFundingSerializer(
            data=federated_data,
            context=self.context,
        )

        self.assertTrue(activity_pub_serializer.is_valid(raise_exception=True))

        crowd_funding = activity_pub_serializer.save()

        self.assertEqual(crowd_funding.donated, Decimal('120.00'))
        self.assertEqual(crowd_funding.donated_currency, 'EUR')


@override_settings(MAPBOX_API_KEY=None)
class ShareActivityGeofeatureLocationTestCase(BluebottleTestCase):
    def setUp(self):
        SitePlatformSettings.objects.create(
            share_activities=['supplier', 'consumer']
        )
        self.country = CountryFactory.create(alpha2_code='NL')

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()
        return {'request': request}

    def create_geofeature(self, mapbox_id, feature_type, name, place_name=None):
        feature = GeoFeature.objects.create(
            mapbox_id=mapbox_id,
            feature_type=feature_type,
        )
        feature.set_current_language('en')
        feature.name = name
        feature.place_name = place_name or name
        feature.save()
        return feature

    def create_geolocation_from_geofeatures(self, primary=None, extra=None, mapbox_id=None):
        place = primary or self.create_geofeature(
            'dXJu-test-amsterdam-place',
            'place',
            'Amsterdam',
            'Amsterdam, Netherlands',
        )
        geolocation = Geolocation(
            country=self.country,
            position=Point(4.9, 52.37),
            formatted_address=None,
            locality=None,
            street=None,
            street_number=None,
            postal_code=None,
            mapbox_id=mapbox_id if mapbox_id is not None else place.mapbox_id,
            geofeature=place,
        )
        geolocation.save(skip_mapbox_sync=True)
        geolocation.geofeatures.add(place, *(extra or []))
        return geolocation, place

    def test_share_funding_uses_geofeature_when_address_fields_are_empty(self):
        geolocation, place = self.create_geolocation_from_geofeatures()
        funding = FundingFactory.create(impact_location=geolocation)

        federated_data = FederatedFundingSerializer(
            instance=funding,
            context=self.context,
        ).data
        location = federated_data['location']
        self.assertEqual(location['name'], place.place_name)
        self.assertEqual(location['place_type'], 'city')
        self.assertEqual(location['address']['locality'], 'Amsterdam')
        self.assertEqual(location['address']['country'], 'NL')
        self.assertEqual(
            location['identifier'],
            [{
                'type': 'PropertyValue',
                'propertyID': 'mapbox-feature-id',
                'value': place.mapbox_id,
            }]
        )

        feature_count = GeoFeature.objects.count()
        activity_pub_serializer = CrowdFundingSerializer(
            data=federated_data,
            context=self.context,
        )
        self.assertTrue(activity_pub_serializer.is_valid(raise_exception=True))

        event = adapter.create_or_update_event(funding)
        self.assertEqual(event.location.name, place.place_name)
        self.assertEqual(event.location.place_type, 'city')
        self.assertEqual(event.location.latitude, geolocation.position.x)
        self.assertEqual(event.location.longitude, geolocation.position.y)
        self.assertEqual(event.location.address.locality, 'Amsterdam')
        self.assertEqual(
            event.location.identifier,
            [{
                'type': 'PropertyValue',
                'propertyID': 'mapbox-feature-id',
                'value': place.mapbox_id,
            }]
        )
        self.assertEqual(GeoFeature.objects.count(), feature_count)

    def test_share_neighborhood_includes_parent_city(self):
        place = self.create_geofeature(
            'dXJu-test-amsterdam-place',
            'place',
            'Amsterdam',
            'Amsterdam, Netherlands',
        )
        neighborhood = self.create_geofeature(
            'dXJu-test-jordaan',
            'neighborhood',
            'Jordaan',
            'Jordaan, Amsterdam, Netherlands',
        )
        geolocation, _ = self.create_geolocation_from_geofeatures(
            primary=neighborhood,
            extra=[place],
        )
        funding = FundingFactory.create(impact_location=geolocation)

        location = FederatedFundingSerializer(
            instance=funding,
            context=self.context,
        ).data['location']
        self.assertEqual(location['place_type'], 'neighborhood')
        self.assertEqual(location['name'], neighborhood.place_name)
        self.assertEqual(location['address']['locality'], 'Amsterdam')

        event = adapter.create_or_update_event(funding)
        self.assertEqual(event.location.place_type, 'neighborhood')
        self.assertEqual(event.location.address.locality, 'Amsterdam')

    def test_share_without_mapbox_id_omits_identifier(self):
        geolocation = Geolocation(
            country=self.country,
            position=Point(4.9, 52.37),
            locality='Amsterdam',
            mapbox_id=None,
        )
        geolocation.save(skip_mapbox_sync=True)
        funding = FundingFactory.create(impact_location=geolocation)

        location = FederatedFundingSerializer(
            instance=funding,
            context=self.context,
        ).data['location']
        self.assertIsNone(location['place_type'])
        self.assertEqual(location['identifier'], [])
        self.assertEqual(location['name'], 'Amsterdam')
        self.assertEqual(location['address']['locality'], 'Amsterdam')

    def test_share_column_based_location_keeps_address_fields(self):
        geolocation = GeolocationFactory.create(country=self.country)
        funding = FundingFactory.create(impact_location=geolocation)

        location = FederatedFundingSerializer(
            instance=funding,
            context=self.context,
        ).data['location']
        self.assertIsNone(location['place_type'])
        self.assertEqual(location['address']['locality'], geolocation.locality)
        self.assertEqual(
            location['identifier'],
            [{
                'type': 'PropertyValue',
                'propertyID': 'mapbox-feature-id',
                'value': geolocation.mapbox_id,
            }]
        )

    def test_linked_location_uses_name_when_locality_missing(self):
        serializer = LinkedLocationSerializer(data={
            'name': 'Amsterdam, Netherlands',
            'latitude': 52.37,
            'longitude': 4.9,
            'address': {
                'locality': None,
                'country': 'NL',
            },
        })
        self.assertTrue(serializer.is_valid(raise_exception=True))
        self.assertEqual(serializer.validated_data['locality'], 'Amsterdam, Netherlands')
        self.assertEqual(
            serializer.validated_data['formatted_address'],
            'Amsterdam, Netherlands',
        )

    def place_payload(self, mapbox_id, place_type='city', name='Amsterdam, Netherlands'):
        return {
            'id': 'https://example.com/place/1',
            'name': name,
            'place_type': place_type,
            'latitude': 52.37,
            'longitude': 4.9,
            'identifier': [{
                'type': 'PropertyValue',
                'propertyID': 'mapbox-feature-id',
                'value': mapbox_id,
            }],
            'address': {
                'id': 'https://example.com/address/1',
                'locality': 'Amsterdam',
                'country': 'NL',
            },
        }

    @override_settings(MAPBOX_API_KEY='test-token')
    @mock.patch('bluebottle.geo.mapbox.lookup_by_mapbox_id')
    def test_consume_place_syncs_mapbox_geofeatures(self, lookup):
        lookup.return_value = {'features': [MAPBOX_V6_ADDRESS_FEATURE]}
        mapbox_id = MAPBOX_V6_ADDRESS_FEATURE['properties']['mapbox_id']
        serializer = LocationSerializer(
            data=self.place_payload(mapbox_id, place_type='address', name='Ouddorp'),
            context=self.context,
        )
        self.assertTrue(serializer.is_valid(raise_exception=True))
        geolocation = serializer.save()

        lookup.assert_called()
        self.assertEqual(geolocation.mapbox_id, mapbox_id)
        self.assertEqual(geolocation.geofeature.feature_type, 'address')
        feature_types = set(geolocation.geofeatures.values_list('feature_type', flat=True))
        self.assertTrue({'address', 'place', 'country'}.issubset(feature_types))

    @override_settings(MAPBOX_API_KEY='test-token')
    @mock.patch('bluebottle.geo.mapbox.lookup_by_mapbox_id')
    def test_linked_location_syncs_mapbox_geofeatures(self, lookup):
        lookup.return_value = {'features': [MAPBOX_V6_ADDRESS_FEATURE]}
        mapbox_id = MAPBOX_V6_ADDRESS_FEATURE['properties']['mapbox_id']
        serializer = LinkedLocationSerializer(
            data=self.place_payload(mapbox_id, place_type='address', name='Ouddorp'),
        )
        self.assertTrue(serializer.is_valid(raise_exception=True))
        geolocation = Geolocation.objects.create(**serializer.validated_data)

        lookup.assert_called()
        self.assertEqual(geolocation.mapbox_id, mapbox_id)
        self.assertEqual(geolocation.geofeature.feature_type, 'address')
        self.assertEqual(geolocation.locality, 'Amsterdam')


class GoodDeedSerializerTest(BluebottleTestCase):
    serializer_class = GoodDeedSerializer

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()
        return {'request': request}

    def test_url_field_included_when_set(self):
        """Test that url field is included in GoodDeedSerializer when it's set."""
        good_deed = GoodDeed.objects.create(
            name='Test Good Deed',
            summary='Test summary',
            url='https://example.com/good-deed'
        )

        serializer = self.serializer_class(
            instance=good_deed, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertEqual(data['url'], 'https://example.com/good-deed')

    def test_url_field_included_when_none(self):
        """Test that url field is included in GoodDeedSerializer even when it's None."""
        good_deed = GoodDeed.objects.create(
            name='Test Good Deed',
            summary='Test summary',
            url=None
        )

        serializer = self.serializer_class(
            instance=good_deed, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertIsNone(data['url'])


class CrowdFundingSerializerTest(BluebottleTestCase):
    serializer_class = CrowdFundingSerializer

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()
        return {'request': request}

    def test_url_field_included_when_set(self):
        """Test that url field is included in CrowdFundingSerializer when it's set."""
        crowd_funding = CrowdFunding.objects.create(
            name='Test Crowd Funding',
            summary='Test summary',
            url='https://example.com/crowd-funding',
            target=1000.00,
            target_currency='EUR'
        )

        serializer = self.serializer_class(
            instance=crowd_funding, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertEqual(data['url'], 'https://example.com/crowd-funding')

    def test_url_field_included_when_none(self):
        """Test that url field is included in CrowdFundingSerializer even when it's None."""
        crowd_funding = CrowdFunding.objects.create(
            name='Test Crowd Funding',
            summary='Test summary',
            url=None,
            target=1000.00,
            target_currency='EUR'
        )

        serializer = self.serializer_class(
            instance=crowd_funding, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertIsNone(data['url'])


class GrantApplicationSerializerTest(BluebottleTestCase):
    serializer_class = GrantApplicationSerializer

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()
        return {'request': request}

    def test_url_field_included_when_set(self):
        """Test that url field is included in GrantApplicationSerializer when it's set."""
        grant_application = GrantApplication.objects.create(
            name='Test Grant Application',
            summary='Test summary',
            url='https://example.com/grant-application',
            target=1000.00,
            target_currency='EUR'
        )

        serializer = self.serializer_class(
            instance=grant_application, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertEqual(data['url'], 'https://example.com/grant-application')

    def test_url_field_included_when_none(self):
        """Test that url field is included in GrantApplicationSerializer even when it's None."""
        grant_application = GrantApplication.objects.create(
            name='Test Grant Application',
            summary='Test summary',
            url=None,
            target=1000.00,
            target_currency='EUR'
        )

        serializer = self.serializer_class(
            instance=grant_application, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertIsNone(data['url'])
