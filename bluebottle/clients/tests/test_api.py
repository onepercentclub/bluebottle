from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from rest_framework import status

from bluebottle.clients import properties
from bluebottle.test.utils import BluebottleTestCase

class ClientSettingsTestCase(BluebottleTestCase):

    def setUp(self):
        super(ClientSettingsTestCase, self).setUp()
        self.settings_url = reverse('settings')

    @override_settings(CLOSED_SITE=False, TOP_SECRET="*****",EXPOSED_TENANT_PROPERTIES=['closed_site'])
    def test_settings_show(self):
        # Check that exposed property is in settings api, and other settings are not shown
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['closedSite'], False)
        self.assertNotIn('topSecret', response.data)


        # Check that exposed setting gets overwritten by client property
        setattr(properties, 'CLOSED_SITE', True)
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['closedSite'], True)

        # Check that previously hidden setting can be exposed
        setattr(properties, 'EXPOSED_TENANT_PROPERTIES', ['closed_site', 'top_secret'])
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('topSecret', response.data)
