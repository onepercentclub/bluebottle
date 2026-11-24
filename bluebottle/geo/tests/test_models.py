from builtins import object
from django.core.exceptions import ValidationError
from django.utils import translation

from bluebottle.offices.tests.factories import LocationFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.geo.models import Region, SubRegion, Country, Location, GeoFeature, Geolocation


class GeoTestsMixin(object):
    def create_region(self, name, numeric_code):
        region = Region(name=name, numeric_code=numeric_code)
        region.save()

        return region

    def create_subregion(self, name, numeric_code, region=None):
        if region is None:
            region, _ = Region.objects.get_or_create(name='test-region',
                                                     numeric_code='200')

        sub_region = SubRegion.objects.create(name=name,
                                              numeric_code=numeric_code,
                                              region=region)

        return sub_region

    def create_country(self, name, numeric_code, sub_region=None, **kwargs):
        if sub_region is None:
            try:
                sub_region = SubRegion.objects.get(name='test-subregion',
                                                   numeric_code='100')
            except SubRegion.DoesNotExist:
                sub_region = self.create_subregion(name='test-subregion',
                                                   numeric_code='100')

        country = Country(name=name, numeric_code=numeric_code,
                          subregion=sub_region)
        for k, v in list(kwargs.items()):
            setattr(country, k, v)

        country.save()

        return country


class GeoTestCase(BluebottleTestCase):
    """ Tests for models in the geo app. """

    def setUp(self):
        super(GeoTestCase, self).setUp()

        # Start with a clean database for each test.
        Country.objects.all().delete()
        SubRegion.objects.all().delete()
        Region.objects.all().delete()

        # A test Region that is needed by the test SubRegion.
        region = Region()
        region.name = "Test Region"
        region.numeric_code = "001"
        region.save()

        # A test SubRegion that is needed by the test Country.
        subregion = SubRegion()
        subregion.name = "Test SubRegion"
        subregion.numeric_code = "002"
        subregion.region = region
        subregion.save()

        # Setup the test Country.
        self.country = Country()
        self.country.name = "Test"
        self.country.subregion = subregion
        self.country.save()

    def test_numberic_code_validation(self):
        """
        Test the numeric code validation.
        """

        # Test a numeric code with letter (capital 'O').
        self.country.numeric_code = "9O1"
        self.assertRaises(ValidationError, self.country.full_clean)

        # Test a numeric code that's too short.
        self.country.numeric_code = "91"
        self.assertRaises(ValidationError, self.country.full_clean)

        # Test a numeric code that's too long.
        self.country.numeric_code = "9198"
        self.assertRaises(ValidationError, self.country.full_clean)

        # Set a correct value and confirm there's no problem.
        self.country.numeric_code = "901"
        self.country.full_clean()

    def test_alpha2_code_validation(self):
        """
        Test the alpha2 code validation.
        """

        # Set a required field.
        self.country.numeric_code = "901"

        # Test an alpha2 code with a number.
        self.country.alpha2_code = "X6"
        self.assertRaises(ValidationError, self.country.full_clean)

        # Test an alpha2 code that's too short.
        self.country.alpha2_code = "X"
        self.assertRaises(ValidationError, self.country.full_clean)

        # Test an alpha2 code that's too long.
        self.country.alpha2_code = "XFF"
        self.assertRaises(ValidationError, self.country.full_clean)

        # Set a correct value and confirm there's no problem.
        self.country.alpha2_code = "XF"
        self.country.full_clean()
        self.country.save()

    def test_alpha3_code_validation(self):
        """
        Test the alpha3 code validation.
        """

        # Set and clear some fields.
        self.country.numeric_code = "901"
        self.country.alpha2_code = ""

        # Test an alpha3 code with a number.
        self.country.alpha3_code = "XX6"
        self.assertRaises(ValidationError, self.country.full_clean)

        # Test an alpha3 code that's too short.
        self.country.alpha3_code = "XF"
        self.assertRaises(ValidationError, self.country.full_clean)

        # Test an alpha3 code that's too long.
        self.country.alpha3_code = "XFFF"
        self.assertRaises(ValidationError, self.country.full_clean)

        # Set a correct value and confirm there's no problem.
        self.country.alpha3_code = "XFF"
        self.country.full_clean()
        self.country.save()


class LocationTestCase(BluebottleTestCase):
    def setUp(self):
        self.location = LocationFactory.create()

        self.to_be_merged = LocationFactory.create()

        self.member = BlueBottleUserFactory.create(location=self.to_be_merged)
        self.activity = DeedFactory.create(office_location=self.to_be_merged)

    def test_merge(self):
        self.location.merge(self.to_be_merged)

        self.assertTrue(self.activity in self.location.activity_set.all())
        self.assertTrue(self.member in self.location.member_set.all())

        for alternate_name in self.to_be_merged.alternate_names:
            self.assertTrue(alternate_name in self.location.alternate_names)

        self.assertRaises(
            Location.DoesNotExist, Location.objects.get, pk=self.to_be_merged.pk
        )


class GeolocationPlaceNameTestCase(BluebottleTestCase):
    def create_geolocation(self, geofeature=None, **kwargs):
        geolocation = Geolocation(geofeature=geofeature, **kwargs)
        geolocation.save(skip_mapbox_sync=True)
        return geolocation

    def create_geofeature(self, language, name='', place_name=''):
        feature = GeoFeature.objects.create(mapbox_id='dXJu-test-feature', feature_type='place')
        feature.set_current_language(language)
        feature.name = name
        feature.place_name = place_name
        feature.save()
        return feature

    def test_without_geofeature_uses_address(self):
        geolocation = self.create_geolocation(formatted_address='Dorpsstraat 1', locality='Assendelft')
        self.assertEqual(geolocation.place_name, 'Dorpsstraat 1')

    def test_without_geofeature_falls_back_to_locality(self):
        geolocation = self.create_geolocation(locality='Assendelft')
        self.assertEqual(geolocation.place_name, 'Assendelft')

    def test_without_geofeature_or_address_returns_placeholder(self):
        self.assertEqual(self.create_geolocation().place_name, '-')

    def test_geofeature_place_name(self):
        feature = self.create_geofeature('en', name='Assendelft', place_name='Assendelft, Netherlands')
        geolocation = self.create_geolocation(geofeature=feature)
        self.assertEqual(geolocation.place_name, 'Assendelft, Netherlands')

    def test_geofeature_falls_back_to_name(self):
        feature = self.create_geofeature('en', name='Assendelft')
        geolocation = self.create_geolocation(geofeature=feature)
        self.assertEqual(geolocation.place_name, 'Assendelft')

    def test_geofeature_falls_back_to_other_language(self):
        feature = self.create_geofeature('fr', name='Assendelft', place_name='Assendelft, France')
        geolocation = Geolocation.objects.get(pk=self.create_geolocation(geofeature=feature).pk)
        with translation.override('en'):
            self.assertEqual(geolocation.place_name, 'Assendelft, France')

    def test_geofeature_without_names_returns_none(self):
        feature = self.create_geofeature('en')
        geolocation = self.create_geolocation(geofeature=feature, locality='Assendelft')
        self.assertFalse(geolocation.place_name)
