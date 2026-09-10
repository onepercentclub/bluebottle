from unittest import mock

from django.urls import reverse
from rest_framework import status

from bluebottle.geo.models import Geolocation, Country
from bluebottle.geo.tests.mapbox_fixtures import MAPBOX_V6_ADDRESS_FEATURE
from bluebottle.geo.widgets import (
    CustomMapboxPointFieldWidget,
    GeolocationMapboxPointFieldWidget,
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory, GeolocationFactory
from bluebottle.test.utils import BluebottleAdminTestCase

mapbox_response = MAPBOX_V6_ADDRESS_FEATURE


@mock.patch(
    'bluebottle.geo.mapbox.lookup_by_mapbox_id',
    return_value={'features': [mapbox_response]}
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

    def test_geolocation_admin(self, mock_lookup):
        if not Country.objects.filter(alpha2_code='NL').exists():
            CountryFactory.create(alpha2_code='NL')
        self.app.set_user(self.user)
        page = self.app.get(self.admin_add_url)
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        form = page.forms[1]
        form.set('position', 'POINT (5.707144274290329 52.504414974388936)')
        form.set('mapbox_id', mapbox_response['properties']['mapbox_id'])
        form.submit()

        geolocation = Geolocation.objects.last()

        self.assertEqual(
            geolocation.mapbox_id,
            mapbox_response['properties']['mapbox_id'],
        )
        self.assertGreater(geolocation.geofeatures.count(), 0)

    def test_map_widgets_use_v6_geocoder(self, mock_lookup):
        for widget_class in (
            CustomMapboxPointFieldWidget,
            GeolocationMapboxPointFieldWidget,
        ):
            media = str(widget_class().media)
            self.assertIn('geolocation-map-widget.js', media)
            self.assertNotIn('mapbox-gl-geocoder', media)

    def test_geolocation_add_uses_v6_search_widget(self, mock_lookup):
        self.app.set_user(self.user)
        page = self.app.get(self.admin_add_url)
        self.assertIn('geolocation-map-widget.js', page.text)
        self.assertNotIn('mapbox-gl-geocoder', page.text)

    def test_admin_search_finds_legacy_v5_location_by_address(self, mock_lookup):
        if not Country.objects.filter(alpha2_code='NL').exists():
            CountryFactory.create(alpha2_code='NL')
        country = Country.objects.get(alpha2_code='NL')
        matching = GeolocationFactory.create(
            locality='Leiden',
            street='Hansenstraat',
            street_number='30',
            formatted_address='Hansenstraat 30, Leiden',
            mapbox_id='address.5221966149504774',
            country=country,
        )
        other = GeolocationFactory.create(
            locality='Amsterdam',
            street='Damrak',
            street_number='1',
            formatted_address='Damrak 1, Amsterdam',
            mapbox_id='address.1111111111111111',
            country=country,
        )

        self.app.set_user(self.user)
        page = self.app.get(
            reverse('admin:geo_geolocation_changelist'),
            params={'q': 'Hansenstraat'},
        )

        self.assertIn(
            reverse('admin:geo_geolocation_change', args=(matching.pk,)),
            page.text,
        )
        self.assertNotIn(
            reverse('admin:geo_geolocation_change', args=(other.pk,)),
            page.text,
        )
