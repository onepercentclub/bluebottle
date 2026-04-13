from django.db import connection
from django.urls import reverse

from bluebottle.activity_pub.models import Person
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.activity_pub.tests.factories import (
    OrganizationFactory, PersonFactory, FollowFactory, DoGoodEventFactory
)
from bluebottle.activity_pub.serializers.json_ld import (
    OrganizationSerializer, PersonSerializer, FollowSerializer, DoGoodEventSerializer
)
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
                self.serializer.to_representation(self.model),
            )
        )


class OrganizationAPITestCase(APITestMixin, BluebottleTestCase):
    factory = OrganizationFactory
    serializer = OrganizationSerializer()


class PersonAPITestCase(APITestMixin, BluebottleTestCase):
    factory = PersonFactory
    serializer = PersonSerializer()


class DoGoodEventAPITestCase(APITestMixin, BluebottleTestCase):
    factory = DoGoodEventFactory
    serializer = DoGoodEventSerializer()
