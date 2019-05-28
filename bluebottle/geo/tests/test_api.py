import json

from django.core.urlresolvers import reverse
from rest_framework import status

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.geo.models import Country, Location
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


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
        response = self.client.get(reverse('country-list'))

        country = response.data[0]
        self.assertEqual(country['id'], self.country_1.id)
        self.assertEqual(country['name'], self.country_1.name)
        self.assertEqual(country['code'], 'GE')


class UsedCountryListTestCase(GeoTestCase):
    def setUp(self):
        super(UsedCountryListTestCase, self).setUp()

        campaign_status = ProjectPhase.objects.get(slug='campaign')
        self.project = ProjectFactory.create(country=self.country_1,
                                             status=campaign_status)

    """
    Test case for ``CountryList`` API view.

    Endpoint: /api/geo/used_countries
    """

    def test_api_used_country_list_endpoint(self):
        """
        Ensure get request returns 200.
        """
        response = self.client.get(reverse('used-country-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


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
                position='10.0,20.0',
                description="Description {}".format(i))
            )

    def test_api_location_list_endpoint(self):
        """
        Ensure get request returns 200.
        """
        response = self.client.get(reverse('location-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.count)
        self.assertEqual(response.data[0]['name'], self.locations[0].name)
        self.assertEqual(response.data[0]['description'], self.locations[0].description)


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

    def test_api_geolocation_create(self):
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
