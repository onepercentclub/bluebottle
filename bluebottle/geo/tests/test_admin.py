from django.urls import reverse
from rest_framework import status

from bluebottle.geo.models import Geolocation, Country
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.mapbox_mocks import MAPBOX_V6_FEATURE
from bluebottle.test.utils import BluebottleAdminTestCase


class GeolocationAdminTest(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super(GeolocationAdminTest, self).setUp()
        self.user = BlueBottleUserFactory(is_staff=True, is_superuser=True)
        self.admin_add_url = reverse('admin:geo_geolocation_add')

    def test_geolocation_admin(self):
        if not Country.objects.filter(alpha2_code='NL').exists():
            CountryFactory.create(alpha2_code='NL')
        self.app.set_user(self.user)
        page = self.app.get(self.admin_add_url)
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        form = page.forms[1]
        form.set('mapbox_id', MAPBOX_V6_FEATURE['id'])
        form.submit()

        geolocation = Geolocation.objects.last()
        self.assertEqual(geolocation.mapbox_id, MAPBOX_V6_FEATURE['id'])
        self.assertTrue(geolocation.features.filter(place_type='country').exists())
