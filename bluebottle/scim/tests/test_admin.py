from django.contrib.admin.sites import AdminSite
from django.test.client import RequestFactory
from django.urls import reverse

from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.scim.admin import SCIMPlatformSettingsAdmin
from bluebottle.scim.models import SCIMPlatformSettings


class MockUser:
    is_active = True

    def __init__(self, perms=None, is_staff=True):
        self.perms = perms or []
        self.is_staff = is_staff
        self.id = 1

    def has_perm(self, perm):
        return perm in self.perms


class PlatformSettingsAdminTest(BluebottleAdminTestCase):
    def setUp(self):
        super(PlatformSettingsAdminTest, self).setUp()

        self.site = AdminSite()
        self.request_factory = RequestFactory()

        self.admin = SCIMPlatformSettingsAdmin(SCIMPlatformSettings, self.site)

        self.scim_settings = SCIMPlatformSettings.objects.create()

        self.request = self.request_factory.post('/', data={'confirm': True})
        self.request.user = MockUser(['scim.change_scimplatformsettings'])

    def test_reset_token(self):
        current_token = self.scim_settings.bearer_token
        response = self.admin.reset_token(self.request, self.scim_settings.pk)

        self.scim_settings.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(self.scim_settings.bearer_token, current_token)

        # Check it shows up in object history
        self.client.force_login(self.superuser)
        url = reverse(
            'admin:scim_scimplatformsettings_history',
            args=(self.scim_settings.pk, )
        )
        response = self.client.get(url)
        self.assertContains(response, 'Reset Token')

    def test_reset_token_no_permission(self):
        self.request.user.perms = []

        current_token = self.scim_settings.bearer_token
        response = self.admin.reset_token(
            self.request, self.scim_settings.pk
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.scim_settings.bearer_token, current_token)

    def test_reset_token_not_confirmed(self):
        current_token = self.scim_settings.bearer_token

        request = self.request_factory.post('/')
        request.user = MockUser(['scim.change_scimplatformsettings'])

        response = self.admin.reset_token(request, self.scim_settings.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.scim_settings.bearer_token, current_token)
