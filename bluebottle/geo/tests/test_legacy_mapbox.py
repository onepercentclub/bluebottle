from unittest import mock

from django.test import TestCase

from bluebottle.geo.legacy_mapbox import (
    extract_house_number_from_address_fields,
    is_legacy_mapbox_id,
    upgrade_mapbox_id,
)
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.mapbox_mocks import MAPBOX_V6_FEATURE


class LegacyMapboxTest(TestCase):
    def test_is_legacy_mapbox_id(self):
        self.assertTrue(is_legacy_mapbox_id('address.8367876655690618'))
        self.assertTrue(is_legacy_mapbox_id('place.12961960'))
        self.assertFalse(is_legacy_mapbox_id('dXJuOm1ieGFkcjp0ZXN0LWFkZHJlc3M'))
        self.assertFalse(is_legacy_mapbox_id(None))

    def test_extract_house_number_from_street_number(self):
        self.assertEqual(extract_house_number_from_address_fields(street_number='20'), '20')

    def test_extract_house_number_from_street(self):
        self.assertEqual(
            extract_house_number_from_address_fields(street='Brouwersdam Buitenzijde 20'),
            '20',
        )

    def test_extract_house_number_from_formatted_address(self):
        self.assertEqual(
            extract_house_number_from_address_fields(
                formatted_address='Brouwersdam Buitenzijde 20, 3253 MM Ouddorp, Netherlands',
            ),
            '20',
        )

    @mock.patch('bluebottle.geo.legacy_mapbox.forward_geocode', return_value=MAPBOX_V6_FEATURE)
    def test_upgrade_mapbox_id(self, mock_forward):
        geolocation = GeolocationFactory.build(
            mapbox_id='place.12961960',
            geofeatures=False,
        )
        new_id = upgrade_mapbox_id(geolocation)
        self.assertEqual(new_id, MAPBOX_V6_FEATURE['id'])
        mock_forward.assert_called()
