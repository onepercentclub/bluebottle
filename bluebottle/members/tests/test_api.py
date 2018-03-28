from django.core.urlresolvers import reverse

from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.utils import BluebottleTestCase


class ProjectPlatformSettingsTestCase(BluebottleTestCase):
    """
    Integration tests for the ProjectPlatformSettings API.
    """
    def test_member_platform_settings(self):
        MemberPlatformSettings.objects.create(
            require_consent=True,
            consent_link='http://example.com'
        )

        response = self.client.get(reverse('settings'))
        self.assertEqual(response.data['platform']['members']['require_consent'], True)
        self.assertEqual(
            response.data['platform']['members']['consent_link'],
            'http://example.com'
        )

    def test_member_platform_settings_default(self):
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.data['platform']['members']['require_consent'], False)
        self.assertEqual(
            response.data['platform']['members']['consent_link'],
            '/pages/terms-and-conditions'
        )
