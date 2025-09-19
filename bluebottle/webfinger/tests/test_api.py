from django.test import Client as TestClient
from django.urls import reverse

from rest_framework import status

from bluebottle.cms.models import SitePlatformSettings
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.test.factory_models.organizations import OrganizationFactory


class WebFingerTestCase(BluebottleTestCase):
    def setUp(self):
        self.client = TestClient()
        self.organization = OrganizationFactory.create()
        self.settings = SitePlatformSettings.objects.create(
            organization=self.organization
        )
        self.url = reverse('webfinger')

        super().setUp()

    def test_get_default_organization(self):
        response = self.client.get(f'{self.url}?resource=http://testserver/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = reverse(
            "activity_pub:organization",
            args=(self.organization.activity_pub_organization.pk, )
        )
        organization_url = f'https://testserver{path}'

        self.assertEqual(
            response.json(),
            {
                'subject': f'acct:{self.organization.slug}@testserver',
                'aliases': [organization_url],
                'links': [{
                    'rel': 'self',
                    'type': "application/activity+json",
                    'href': organization_url
                }]
            }
        )
