from unittest import mock

from django.urls import reverse
from rest_framework import status

from bluebottle.geo.models import Geolocation, Country
from bluebottle.geo.tests.mapbox_fixtures import MAPBOX_V6_ADDRESS_FEATURE
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.utils import BluebottleAdminTestCase

mapbox_response = MAPBOX_V6_ADDRESS_FEATURE


@mock.patch(
    'bluebottle.geo.models.Geolocation.reverse_geocode',
    return_value=mapbox_response
)
class GeolocationAdminTest(BluebottleAdminTestCase):
    """
    Test Geolocation admin
    """
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super(GeolocationAdminTest, self).setUp()
        self.user = BlueBottleUserFactory(is_staff=True, is_superuser=True)
        self.admin_add_url = reverse('admin:geo_geolocation_add')

    def test_geolocation_admin(self, mock_reverse_geocode):
        if not Country.objects.filter(alpha2_code='NL').exists():
            CountryFactory.create(alpha2_code='NL')
        self.app.set_user(self.user)
        page = self.app.get(self.admin_add_url)
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        form = page.forms[1]
        form.set('position', 'POINT (5.707144274290329 52.504414974388936)')
        form.submit()

        geolocation = Geolocation.objects.last()

        self.assertEqual(
            geolocation.formatted_address,
            'Brouwersdam Buitenzijde 20, 3253 MM Ouddorp, Netherlands'
        )
        self.assertEqual(
            geolocation.locality,
            'Ouddorp'
        )
