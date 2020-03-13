import json

from django.core.urlresolvers import reverse
from rest_framework import status

from bluebottle.geo.models import Country, Location
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.events.tests.factories import EventFactory
from bluebottle.assignments.tests.factories import AssignmentFactory
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
    """
    Test case for ``CountryList`` API view.

    Endpoint: /api/geo/used_countries
    """
    def setUp(self):
        super(UsedCountryListTestCase, self).setUp()

        self.event = EventFactory.create(
            review_status='approved', status='new'
        )
        EventFactory.create(
            review_status='approved', status='new', location=self.event.location
        )

        self.assignment = AssignmentFactory.create(
            review_status='approved', status='new'
        )

        EventFactory.create(
            review_status='submitted', status='in_review'
        )
        self.initiative = InitiativeFactory.create(
            status='approved'
        )

    def test_api_used_country_list_endpoint(self):
        """
        Ensure get request returns 200.
        """
        response = self.client.get(reverse('used-country-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 3)

        countries = [country['id'] for country in response.json()]

        self.assertTrue(self.initiative.place.country.pk in countries)
        self.assertTrue(self.event.location.country.pk in countries)
        self.assertTrue(self.assignment.location.country.pk in countries)


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
