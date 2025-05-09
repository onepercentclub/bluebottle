import json
from builtins import range
from unittest import mock

from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status

from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.geo.models import Country, Location
from bluebottle.geo.serializers import InitiativeCountrySerializer, PlaceSerializer
from bluebottle.geo.tests.test_admin import mapbox_response
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import (
    CountryFactory, GeolocationFactory, LocationFactory, PlaceFactory
)
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient, APITestCase
from bluebottle.time_based.tests.factories import DateActivityFactory, DeadlineActivityFactory, DateActivitySlotFactory


class GeoTestCase(BluebottleTestCase):
    """
    Base class for test cases for ``slide`` module.

    The testing classes for ``slide`` module related to the API must
    subclass this.
    """
    fixtures = ['geo_data.json']

    def setUp(self):
        super(GeoTestCase, self).setUp()
        self.init_projects()
        self.country_1 = Country.objects.get(translations__name="Abkhazia")


class CountryListTestCase(GeoTestCase):
    """
    Test case for ``CountryList`` API view.

    Endpoint: /api/geo/countries
    """

    def test_api_country_list_endpoint(self):
        """
        Ensure get request returns 200.
        """
        response = self.client.get(reverse('country-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 245)

    def test_api_country_list_data(self):
        """
        Ensure get request returns record with correct data.
        """
        response = self.client.get(
            reverse('country-list'),
            HTTP_X_APPLICATION_LANGUAGE='nl'
        )

        countries = response.data
        self.assertTrue('Abchazië' in [c['name'] for c in countries])
        self.assertTrue('Zwitserland' in [c['name'] for c in countries])


class UsedCountryListTestCase(GeoTestCase):
    """
    Test case for ``CountryList`` API view.

    Endpoint: /api/geo/used_countries
    """

    def setUp(self):
        super(UsedCountryListTestCase, self).setUp()

        belgium = Country.objects.get(alpha2_code="BE")
        location_be = GeolocationFactory.create(country=belgium)

        bulgaria = Country.objects.get(alpha2_code="BG")
        location_bg = GeolocationFactory.create(country=bulgaria)

        germany = Country.objects.get(alpha2_code="DE")
        location_de = GeolocationFactory.create(country=germany)

        turkey = Country.objects.get(alpha2_code="TR")
        location_tr = GeolocationFactory.create(country=turkey)

        initiative = InitiativeFactory.create(
            status='approved',
            place=location_tr
        )

        activity = DateActivityFactory.create(
            status='open',
            initiative=initiative,
            slots=[]
        )
        DateActivitySlotFactory.create(
            activity=activity,
            location=location_be
        )

        activity = DateActivityFactory.create(
            status='full',
            initiative=initiative,
            slots=[]
        )
        DateActivitySlotFactory.create(
            activity=activity,
            location=location_bg
        )

        DeadlineActivityFactory.create(
            status='draft',
            location=location_de
        )

        activity = DateActivityFactory.create(
            status='submitted',
            initiative=initiative,
            slots=[]
        )
        DateActivitySlotFactory.create(
            activity=activity,
            location=location_de
        )

        FundingFactory.create(
            initiative=initiative,
            status='open'
        )

    def test_api_used_country_list_endpoint(self):
        response = self.client.get(reverse('country-list'), {'filter[used]': True, '_': now()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 3)
        countries = [country['id'] for country in response.json()]
        self.assertEqual(len(countries), 3)

    def test_api_used_country_list_endpoint_with_offices(self):
        ireland = Country.objects.filter(translations__name="Ireland").first()
        office = LocationFactory.create(country=ireland)
        InitiativeFactory.create(location=office, status='approved', place=None)
        response = self.client.get(reverse('country-list'), {'filter[used]': True, '_': now()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)
        countries = [country['id'] for country in response.json()]
        self.assertEqual(len(countries), 4)


class LocationListTestCase(GeoTestCase):
    """
    Test case for ``LocationList`` API view.

    Endpoint: /api/geo/locations
    """

    def setUp(self):
        super(GeoTestCase, self).setUp()

        self.count = 10
        self.locations = []
        for i in range(0, self.count):
            self.locations.append(Location.objects.create(
                name="Name {}".format(i),
                position=Point(20.0, 10.0),
                description="Description {}".format(i))
            )

    def test_api_location_detail_endpoint(self):
        location = self.locations[0]
        response = self.client.get(reverse('office-detail', args=(location.id, )))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data['attributes']['name'], self.locations[0].name)
        self.assertEqual(data['attributes']['description'], self.locations[0].description)

        static_map_url = data['attributes']['static-map-url']
        self.assertTrue(
            static_map_url.startswith('https://maps.googleapis.com/maps/api/staticmap?')
        )
        self.assertTrue(
            'signature=' in static_map_url
        )
        self.assertTrue(
            'center=10' in static_map_url
        )

    def test_api_location_closed_platform(self):
        member_settings = MemberPlatformSettings.objects.get()
        member_settings.closed = True
        member_settings.save()

        location = self.locations[0]
        response = self.client.get(reverse('office-detail', args=(location.id, )))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GeolocationCreateTestCase(GeoTestCase):
    """
    Test case for ``GeolocationList`` API view.
    Endpoint: /api/geo/geolocations
    """

    def setUp(self):
        super(GeoTestCase, self).setUp()
        self.country = CountryFactory.create()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory.create()

    @mock.patch(
        'bluebottle.geo.models.Geolocation.reverse_geocode',
        return_value=mapbox_response
    )
    def test_api_geolocation_create(self, mock_reverse_geocode):
        """
        Ensure post request returns 201.
        """
        data = {
            "data": {
                "type": "geolocations",
                "attributes": {
                    "position": {"latitude": 43.0579025, "longitude": 23.6851594},
                },
                "relationships": {
                    "country": {
                        "data": {
                            "type": "countries",
                            "id": self.country.id
                        }
                    }
                }
            }
        }
        response = self.client.post(reverse('geolocation-list'), json.dumps(data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['position'],
                         {'latitude': 43.0579025, 'longitude': 23.6851594})

        static_map_url = response.data['static_map_url']
        self.assertTrue(
            static_map_url.startswith('https://maps.googleapis.com/maps/api/staticmap?')
        )
        self.assertTrue(
            'signature=' in static_map_url
        )
        self.assertTrue(
            'center={latitude},{longitude}'.format(**response.data['position']) in static_map_url
        )


class JSONAPICountryListTestCase(APITestCase):

    def setUp(self):
        super().setUp()

        self.serializer = InitiativeCountrySerializer
        CountryFactory.create_batch(20)

        self.url = reverse('new-country-list')

    def test_get(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        self.assertSize(20)


class PlaceDetailTestCase(APITestCase):

    def setUp(self):
        super().setUp()

        self.serializer = PlaceSerializer

        self.place = PlaceFactory.create()
        self.user = BlueBottleUserFactory.create(place=self.place)

        self.url = reverse('place-detail', args=(self.place.pk, ))

    def test_get(self):
        self.perform_get(user=self.user)

        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('locality', self.place.locality)

    def test_get_anonymous(self):
        self.perform_get()
        # Share places
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_get_other_user(self):
        self.perform_get(user=BlueBottleUserFactory.create())
        # Share places
        self.assertStatus(status.HTTP_403_FORBIDDEN)
