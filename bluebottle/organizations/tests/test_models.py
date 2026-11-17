from bluebottle.cms.models import SitePlatformSettings
from bluebottle.cms.utils.color_contrast import DARK_NEUTRAL, WHITE, ensure_readable_fill
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.utils import BluebottleTestCase


class OrganizationColorTestCase(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        SitePlatformSettings.objects.update(accessible_colours=False)

    def test_text_color_white_on_dark(self):
        organization = OrganizationFactory.create(color='#00305E')

        self.assertEqual(organization.background_color, '#00305E')
        self.assertEqual(organization.text_color, WHITE)

    def test_text_color_dark_on_light(self):
        organization = OrganizationFactory.create(color='#FFFFFF')

        self.assertEqual(organization.background_color, '#FFFFFF')
        self.assertEqual(organization.text_color, DARK_NEUTRAL)

    def test_accessible_colours_darkens_light_fill(self):
        SitePlatformSettings.objects.update(accessible_colours=True)
        organization = OrganizationFactory.create(color='#A2A2A2')

        expected = ensure_readable_fill('#A2A2A2')
        self.assertEqual(organization.background_color, expected)
        self.assertNotEqual(organization.background_color, '#A2A2A2')
        self.assertEqual(organization.text_color, WHITE)

    def test_no_color_returns_none(self):
        organization = OrganizationFactory.create(color=None)
        self.assertIsNone(organization.background_color)
        self.assertIsNone(organization.text_color)
