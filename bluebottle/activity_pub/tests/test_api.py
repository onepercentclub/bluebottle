from bluebottle.cms.models import SitePlatformSettings
from bluebottle.activity_pub.tests.factories import (
    OrganizationFactory, PersonFactory, DoGoodEventFactory
)
from bluebottle.activity_pub.serializers import ActivityPubSerializer
from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.test.utils import JSONAPITestClient, BluebottleTestCase


class APITestMixin:
    renderer = JSONLDRenderer()

    def setUp(self):
        super().setUp()

        site_settings = SitePlatformSettings.load()
        site_settings.share_activities = ['supplier', 'consumer']
        site_settings.save()

        self.json_api_client = JSONAPITestClient()

        self.model = self.factory.create(iri=None)

    def test_get(self):
        response = self.client.get(self.model.pub_url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.content,
            self.renderer.render(
                ActivityPubSerializer().to_representation(self.model),
            )
        )


class OrganizationAPITestCase(APITestMixin, BluebottleTestCase):
    factory = OrganizationFactory


class PersonAPITestCase(APITestMixin, BluebottleTestCase):
    factory = PersonFactory


class DoGoodEventAPITestCase(APITestMixin, BluebottleTestCase):
    factory = DoGoodEventFactory
