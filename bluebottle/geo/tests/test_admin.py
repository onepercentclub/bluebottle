from unittest import mock

from django.urls import reverse
from rest_framework import status

from bluebottle.geo.models import Geolocation, Country
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase

mapbox_response = {
    'id': 'address.8367876655690618',
    'type': 'Feature',
    'place_type': ['address'],
    'relevance': 1,
    'properties': {
        'accuracy': 'rooftop',
        'mapbox_id': 'dXJuOm1ieGFkcjowYzM5NTBjMi0wMjNhLTQxNTUtOTRmOS1kZTFmZDcxOWQwMTY'
    },
    'text': 'Brouwersdam Buitenzijde',
    'place_name': 'Brouwersdam Buitenzijde 20, 3253 MM Ouddorp, Netherlands',
    'center': [3.851166, 51.762731],
    'geometry': {'type': 'Point', 'coordinates': [3.851166, 51.762731]},
    'address': '20',
    'context': [
        {'id': 'postcode.8367876655690618', 'text': '3253 MM'},
        {'id': 'place.12961960', 'mapbox_id': 'dXJuOm1ieHBsYzp4Y2lv',
         'wikidata': 'Q21060', 'text': 'Ouddorp'},
        {'id': 'region.25768', 'mapbox_id': 'dXJuOm1ieHBsYzpaS2c',
         'wikidata': 'Q694', 'short_code': 'NL-ZH', 'text': 'South Holland'},
        {'id': 'country.8872', 'mapbox_id': 'dXJuOm1ieHBsYzpJcWc',
         'wikidata': 'Q55', 'short_code': 'nl', 'text': 'Netherlands'}
    ]
}


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
        self.app.set_user(self.user)
        page = self.app.get(self.admin_add_url)
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        form = page.forms[0]
        form.set('position', 'POINT (5.707144274290329 52.504414974388936)')
        form.submit()
        Country.objects.get_or_create(alpha2_code='NL')

        geolocation = Geolocation.objects.last()

        self.assertEqual(
            geolocation.formatted_address,
            'Brouwersdam Buitenzijde 20, 3253 MM Ouddorp, Netherlands'
        )
        self.assertEqual(
            geolocation.locality,
            'Ouddorp'
        )
