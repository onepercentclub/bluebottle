from django.test import TestCase

from bluebottle.geo.location_display import format_geolocation_display, format_location_display
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.test.factory_models.geo import CountryFactory, GeolocationFactory


class FormatLocationDisplayTestCase(TestCase):
    def setUp(self):
        self.country = CountryFactory.create(name='Netherlands', alpha2_code='NL')
        self.geolocation = GeolocationFactory.create(
            country=self.country,
            locality='Community Center',
        )

    def test_location_name_uses_geolocation_locality(self):
        settings = InitiativePlatformSettings.load()
        settings.location_features = ['location_name', 'country']
        settings.save()

        formatted = format_geolocation_display(self.geolocation)

        self.assertEqual(formatted, 'Community Center, NL')

    def test_location_name_without_geofeatures(self):
        self.geolocation.features.clear()
        settings = InitiativePlatformSettings.load()
        settings.location_features = ['location_name']
        settings.save()

        formatted = format_geolocation_display(self.geolocation)

        self.assertEqual(formatted, 'Community Center')

    def test_address_falls_back_to_formatted_address(self):
        self.geolocation.features.clear()
        settings = InitiativePlatformSettings.load()
        settings.location_features = ['address', 'place']
        settings.save()

        formatted = format_geolocation_display(self.geolocation)

        self.assertEqual(formatted, self.geolocation.formatted_address)

    def test_es_geofeature_dicts_support_location_name(self):
        settings = InitiativePlatformSettings.load()
        settings.location_features = ['location_name', 'place', 'country']
        settings.save()

        geofeatures = [
            {
                'place_type': 'place',
                'name': 'Leiden',
                'language': 'en',
            },
            {
                'place_type': 'country',
                'name': 'Netherlands',
                'code': 'NL',
                'language': 'en',
            },
        ]

        formatted = format_location_display(
            geofeatures,
            locality='Community Center',
            formatted_address='Dam 1, Leiden',
        )

        self.assertEqual(formatted, 'Community Center, Leiden, NL')

    def test_elasticsearch_attrdict_geofeatures(self):
        from elasticsearch_dsl.utils import AttrDict

        settings = InitiativePlatformSettings.load()
        settings.location_features = ['location_name', 'place', 'country']
        settings.save()

        geofeatures = [
            AttrDict({
                'place_type': 'place',
                'name': 'Leiden',
                'language': 'en',
            }),
            AttrDict({
                'place_type': 'country',
                'name': 'Netherlands',
                'code': 'NL',
                'language': 'en',
            }),
        ]

        formatted = format_location_display(
            geofeatures,
            locality='Community Center',
            formatted_address='Dam 1, Leiden',
        )

        self.assertEqual(formatted, 'Community Center, Leiden, NL')
