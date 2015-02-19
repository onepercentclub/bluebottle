from django.core.urlresolvers import reverse
from rest_framework import status

from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.geo.models import Country
from bluebottle.test.utils import BluebottleTestCase


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

        self.country_1 = Country.objects.get(name="Afghanistan")
        self.country_2 = Country.objects.get(name="Belgium")


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
        self.assertEqual(len(response.data), 242)


    def test_api_country_list_data(self):
        """
        Ensure get request returns record with correct data.
        """
        response = self.client.get(reverse('country-list'))

        country = response.data[0]
        self.assertEqual(country['id'], 1)
        self.assertEqual(country['name'], 'Afghanistan')
        self.assertEqual(country['oda'], True)
        self.assertEqual(country['code'], 'AF')


class UsedCountryListTestCase(GeoTestCase):

    def setUp(self):
        super(UsedCountryListTestCase, self).setUp()

        campaign_status = ProjectPhase.objects.get(slug='campaign')
        self.project = ProjectFactory.create(country=self.country_1, status=campaign_status)

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
