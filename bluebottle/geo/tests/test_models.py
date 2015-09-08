from django.core.exceptions import ValidationError

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.geo.models import Region, SubRegion, Country


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
        for k, v in kwargs.items():
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
