from django.contrib.admin.sites import AdminSite
from django.contrib.gis.geos import Point
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from bluebottle.geo.admin import LocationAdmin
from bluebottle.geo.models import Location, Geolocation
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase


class LocationAdminTest(BluebottleTestCase):
    """ Tests for models in the geo app. """

    def setUp(self):
        super(LocationAdminTest, self).setUp()
        self.init_projects()
        self.location = Location.objects.create(
            name='Amsterdam',
            position='52.3702157,52.3702157'
        )
        self.site = AdminSite()
        self.admin = LocationAdmin(Location, self.site)
        ProjectFactory(location=self.location)

    def test_projects_link(self):
        """
        Test the numeric code validation.
        """
        projects_link = self.admin.projects(self.location)
        self.assertTrue('>1<' in projects_link)
        self.assertTrue(
            '/en/admin/projects/project/?location={}'.format(self.location.id) in projects_link
        )


class GeolocationAdminTest(TestCase):
    """
    Test Geolocation admin
    """

    def setUp(self):
        super(GeolocationAdminTest, self).setUp()
        self.country = CountryFactory.create()
        self.user = BlueBottleUserFactory(is_staff=True, is_superuser=True)
        self.admin_add_url = reverse('admin:geo_geolocation_add')

    def test_geolocation_admin(self):
        self.client.force_login(self.user)
        response = self.client.get(self.admin_add_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Use the position format as used by point widget
        data = {
            'position': 'POINT (23.6765763312 43.0681866356)',
            'country': self.country.id
        }

        response = self.client.post(self.admin_add_url, data, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = list(get_messages(response.wsgi_request))
        geolocation = Geolocation.objects.last()
        expected = 'The geolocation "<a href="/en/admin/geo/geolocation/{}/change/">' \
                   '{}</a>" was added successfully.'.format(geolocation.id, geolocation.country.name)
        self.assertEquals(str(messages[0]), expected)
        self.assertEquals(geolocation.position.wkt, Point(23.6765763312, 43.0681866356).wkt)
