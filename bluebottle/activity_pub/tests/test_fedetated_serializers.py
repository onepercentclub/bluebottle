import json
from urllib.parse import urlparse
from operator import attrgetter
from io import BytesIO

import mock
import httmock
from django.test import RequestFactory
from requests import Response

from bluebottle.cms.models import SitePlatformSettings

from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.models import (
    GoodDeed, CrowdFunding, GrantApplication, ActivityPubModel, Inbox, Outbox, PublicKey
)
from bluebottle.activity_pub.serializers.base import (
    ActivityPubSerializer, FederatedObjectSerializer
)

from bluebottle.cms.models import SitePlatformSettings
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import DateActivityFactory, DateActivitySlotFactory

from bluebottle.test.factory_models.organizations import OrganizationFactory as BlueobttoeOrganizationFactory
from bluebottle.activity_pub.tests.factories import OrganizationFactory, PersonFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class FederatedSerializerTestCase:
    def setUp(self):
        self.renderer = JSONLDRenderer()

        site_settings = SitePlatformSettings.load()
        site_settings.share_activities = ['supplier', 'consumer']
        site_settings.save()

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()

        return {'request': request}

    def test_to_representation(self):
        self.instance = self.factory.create()
        self.serializer = FederatedObjectSerializer(
            instance=self.instance, context=self.context
        )

    def test_create_activity_pub_resource(self):
        self.instance = self.factory.create()
        serializer = FederatedObjectSerializer(instance=self.instance, context=self.context)

        activity_pub_serializer = ActivityPubSerializer(
            data=serializer.data, origin=serializer.instance
        )
        self.assertTrue(activity_pub_serializer.is_valid())

        activity_pub_serializer.save()
        self.activity_pub_instance = activity_pub_serializer.instance

        self.assertEqual(self.instance, self.activity_pub_instance.federated_object)

    def test_create_federated_model(self):
        self.activity_pub_instance = self.activity_pub_factory.create()

        serializer = ActivityPubSerializer(
            instance=self.activity_pub_instance, context=self.context
        )

        federated_serializer = FederatedObjectSerializer(
            data=serializer.data, origin=self.activity_pub_instance
        )
        self.assertTrue(federated_serializer.is_valid())

        federated_serializer.save()
        self.instance = federated_serializer.instance
        self.instance.refresh_from_db()

        self.assertEqual(
            self.instance.origin, self.activity_pub_instance
        )


class OrganizationSerializerTestCase(FederatedSerializerTestCase, BluebottleTestCase):
    factory = BlueobttoeOrganizationFactory
    activity_pub_factory = OrganizationFactory

    def test_to_representation(self):
        super().test_to_representation()

        self.assertEqual(
            self.instance.name, self.serializer.data['name']
        )

    def test_create_activity_pub_resource(self):
        super().test_create_activity_pub_resource()

        self.assertEqual(
            self.instance.name, self.activity_pub_instance.name
        )


class PersonSerializerTestCase(FederatedSerializerTestCase, BluebottleTestCase):
    factory = BlueBottleUserFactory
    activity_pub_factory = PersonFactory

    def test_to_representation(self):
        super().test_to_representation()

        self.assertEqual(
            self.instance.first_name, self.serializer.data['given_name']
        )
        self.assertEqual(
            self.instance.last_name, self.serializer.data['family_name']
        )
        self.assertEqual(
            self.instance.full_name, self.serializer.data['name']
        )

    def test_create_activity_pub_resource(self):
        super().test_create_activity_pub_resource()

        self.assertEqual(
            self.instance.first_name, self.activity_pub_instance.given_name
        )
        self.assertEqual(
            self.instance.first_name, self.activity_pub_instance.family_name
        )
        self.assertEqual(
            self.instance.full_name, self.activity_pub_instance.name
        )
