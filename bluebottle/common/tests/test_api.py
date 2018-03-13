from bluebottle.common.models import CommonPlatformSettings
from bluebottle.test.utils import BluebottleTestCase
from django.urls.base import reverse


class TestLockDown(BluebottleTestCase):
    """
    Test that the lock-down works
    """

    def setUp(self):
        super(TestLockDown, self).setUp()
        self.config_url = reverse('settings')
        self.lock_down_url = reverse('lock-down')
        self.init_projects()

    def test_without_lockdown_settings(self):
        response = self.client.get(self.config_url)
        self.assertEquals(response.status_code, 200)

    def test_without_lockdown(self):
        CommonPlatformSettings.objects.create(lockdown=False, lockdown_password='sssht')
        response = self.client.get(self.config_url)
        self.assertEquals(response.status_code, 200)

    def test_with_lockdown(self):
        CommonPlatformSettings.objects.create(lockdown=True, lockdown_password='sssht')
        response = self.client.get(self.config_url)
        self.assertEquals(response.status_code, 401)

    def test_unlocking_lockdown(self):
        common_settings = CommonPlatformSettings.objects.create(lockdown=True, lockdown_password='sssht')
        token = common_settings.token
        response = self.client.get(self.config_url, HTTP_X_LOCKDOWN_TOKEN=token)
        self.assertEquals(response.status_code, 200)
