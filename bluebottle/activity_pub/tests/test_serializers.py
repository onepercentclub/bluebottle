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
from bluebottle.activity_pub.serializers.federated_activities import FederatedDateActivitySerializer
from bluebottle.activity_pub.serializers.json_ld import (
    DoGoodEventSerializer, GoodDeedSerializer, CrowdFundingSerializer, GrantApplicationSerializer,
)
from bluebottle.activity_pub.serializers.base import ActivityPubSerializer
from bluebottle.activity_pub.tests.factories import (
    DoGoodEventFactory, OrganizationFactory, FollowFactory
)
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import DateActivityFactory, DateActivitySlotFactory


class JSONLDSerializerTestCase:
    mocks = []

    def setUp(self):
        self.renderer = JSONLDRenderer()

        site_settings = SitePlatformSettings.load()
        site_settings.share_activities = ['supplier', 'consumer']
        site_settings.save()

        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as image_file:
            self.mock_image_response = Response()
            self.mock_image_response.raw = BytesIO(image_file.read())
            self.mock_image_response.status_code = 200

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()

        return {'request': request}

    def test_to_representation(self):
        self.instance = self.factory.create()
        serializer = ActivityPubSerializer(instance=self.instance, context=self.context)

        representation = serializer.data

        self.assertEqual(
            representation['type'], self.factory._meta.model.__name__
        )

        for key, attr in self.mapping.items():
            expected = attrgetter(attr)(self.instance)
            if (
                isinstance(representation[key], str) and
                isinstance(expected, ActivityPubModel)
            ):
                self.assertEqual(
                    representation[key],
                    expected.pub_url
                )
            else:
                self.assertEqual(
                    representation[key],
                    expected
                )

    def test_create(self):
        with httmock.HTTMock(*self.mocks):
            serializer = ActivityPubSerializer(data=self.data, context=self.context)
            serializer.is_valid()

        self.assertTrue(serializer.is_valid())

        self.instance = serializer.save()
        self.check(serializer)

    def check(self, serializer):
        for key, attr in self.mapping.items():
            expected = attrgetter(attr)(self.instance)
            if isinstance(expected, ActivityPubModel):
                expected = expected.pub_url

            self.assertEqual(
                serializer.initial_data[key],
                expected
            )

    def test_update(self):
        self.test_create()
        self.update()

        with httmock.HTTMock(*self.mocks):
            serializer = ActivityPubSerializer(
                data=self.data, instance=self.instance, context=self.context
            )
            self.assertTrue(serializer.is_valid())

        serializer.save()
        self.check(serializer)


class OrganizationSerializerTestCase(JSONLDSerializerTestCase, BluebottleTestCase):
    factory = OrganizationFactory

    mapping = {
        'id': 'pub_url',
        'name': 'name',
        'content': 'content',
        'summary': 'summary',
        'outbox': 'outbox',
        'inbox': 'inbox',
    }

    def setUp(self):
        self.data = {
            'type': 'Organization',
            'id': 'http://example.com/api/json-ld/organization/35',
            'inbox': 'http://example.com/api/json-ld/inbox/32',
            'outbox': 'http://example.com/api/json-ld/outbox/33',
            'public_key': {
                'id': 'http://example.com/api/json-ld/publickey/34',
                'public_key_pem': 'some-pem-data'
            },
            'name': 'Organization name',
            'summary': 'Organization summart',
            'content': 'Organization content',
        }
        super().setUp()

    def update(self):
        self.data['name'] = 'new name'
        self.data['public_key']['public_key_pem'] = 'new public_key'

    def test_create_existing_relations(self):
        Inbox(iri=self.data['inbox']).save()
        Outbox(iri=self.data['outbox']).save()
        PublicKey(
            iri=self.data['public_key'],
            public_key_pem=self.data['public_key']['public_key_pem']
        ).save()

        self.test_create()


def mock_rsource(model):
    @httmock.urlmatch(method="GET", path=urlparse(self.model.iri).path)
    def actor_mock(url, request):
        data = ActivityPubSerializer(instance=model).data

        return {
            'content': self.renderer.render(data),
            'status_code': 200,
            'headers': {'content-type': 'application/ld+json'}
        }


class FollowSerializerTestCase(JSONLDSerializerTestCase, BluebottleTestCase):
    factory = FollowFactory

    mapping = {
        'id': 'pub_url',
        'actor': 'actor',
        'object': 'object',
        'adoption_type': 'adoption_type',
    }

    def setUp(self):
        self.actor = OrganizationFactory.create(
            iri='http://example.com/api/json-ld/actor/32'
        )

        self.object = OrganizationFactory.create(
            iri='http://example.com/api/json-ld/actor/33'
        )

        self.next_object = OrganizationFactory.create(
            iri='http://example.com/api/json-ld/actor/34'
        )

        self.data = {
            'type': 'Follow',
            'id': 'http://example.com/api/json-ld/follow/35',
            'actor': self.actor.iri,
            'object': self.object.iri,
            'adoption_type': 'template',
        }
        super().setUp()

    @property
    def mocks(self):
        return [mock_resource(model) for model in [self.actor, self.object, next_object]]

    def update(self):
        self.data['object'] = self.next_object.iri


class DoGoodEventSerializerTestCase(BluebottleTestCase):
    activity_pub_serializer = DoGoodEventSerializer
    federated_serializer = FederatedDateActivitySerializer
    factory = DateActivityFactory
    activity_pub_factory = DoGoodEventFactory

    def setUp(self):
        self.settings = SitePlatformSettings.objects.create(
            share_activities=['supplier', 'consumer']
        )
        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as image_file:
            self.mock_image_response = Response()
            self.mock_image_response.raw = BytesIO(image_file.read())
            self.mock_image_response.status_code = 200

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()

        return {'request': request}

    def test_to_json_ld(self):
        model = self.factory.create()
        federated_serializer = self.federated_serializer(
            instance=model,
            context=self.context
        )

        activity_pub_serializer = self.activity_pub_serializer(
            data=federated_serializer.data,
            context=self.context
        )

        self.assertTrue(activity_pub_serializer.is_valid(raise_exception=True))

        do_good_event = activity_pub_serializer.save()

        self.assertEqual(do_good_event.name, model.title)
        self.assertEqual(do_good_event.summary, model.description.html)
        self.assertEqual(do_good_event.sub_event.count(), model.slots.count())

    def test_to_json_ld_slots_keep_individual_locations(self):
        model = self.factory.create(slots=[])
        first_location = GeolocationFactory.create()
        second_location = GeolocationFactory.create()
        DateActivitySlotFactory.create(activity=model, location=first_location)
        DateActivitySlotFactory.create(activity=model, location=second_location)

        federated_serializer = self.federated_serializer(
            instance=model,
            context=self.context
        )

        activity_pub_serializer = self.activity_pub_serializer(
            data=federated_serializer.data,
            context=self.context
        )

        self.assertTrue(activity_pub_serializer.is_valid(raise_exception=True))
        do_good_event = activity_pub_serializer.save()

        serialized_locations = {
            (
                slot.location.latitude,
                slot.location.longitude
            )
            for slot in do_good_event.sub_event.all()
        }
        expected_locations = {
            (first_location.position.x, first_location.position.y),
            (second_location.position.x, second_location.position.y),
        }
        self.assertSetEqual(serialized_locations, expected_locations)

    def test_to_json_ld_already_exists(self):
        model = self.factory.create()
        federated_serializer = self.federated_serializer(
            instance=model,
            context=self.context
        )

        activity_pub_serializer = self.activity_pub_serializer(
            data=federated_serializer.data,
            context=self.context
        )

        self.assertTrue(activity_pub_serializer.is_valid(raise_exception=True))

        do_good_event = activity_pub_serializer.save()

        self.activity_pub_serializer(instance=do_good_event, data=federated_serializer.data, context=self.context)
        self.assertTrue(activity_pub_serializer.is_valid(raise_exception=True))
        do_good_event = activity_pub_serializer.save()

        self.assertEqual(do_good_event.name, model.title)
        self.assertEqual(do_good_event.summary, model.description.html)
        self.assertEqual(do_good_event.sub_event.count(), model.slots.count())

    def test_to_federated_activity(self):
        activity_pub_model = self.activity_pub_factory.create(iri='http://example.com')

        federated_serializer = self.activity_pub_serializer(
            instance=activity_pub_model, context=self.context
        )
        serializer = self.federated_serializer(
            data=federated_serializer.data, context=self.context
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))

        with mock.patch('requests.get', return_value=self.mock_image_response):
            activity = serializer.save()

        self.assertEqual(activity.title, activity_pub_model.name)
        self.assertEqual(activity.description.html, activity_pub_model.summary)
        self.assertEqual(activity.slots.count(), activity_pub_model.sub_event.count())

    def test_to_federated_activity_already_exists(self):
        activity_pub_model = self.activity_pub_factory.create(iri='http://example.com')

        federated_serializer = self.activity_pub_serializer(
            instance=activity_pub_model, context=self.context
        )

        serializer = self.federated_serializer(
            data=federated_serializer.data, context=self.context
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))

        with mock.patch('requests.get', return_value=self.mock_image_response):
            activity = serializer.save()

        serializer = self.federated_serializer(
            instance=activity, data=federated_serializer.data, context=self.context
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))

        with mock.patch('requests.get', return_value=self.mock_image_response):
            activity = serializer.save()

        self.assertEqual(activity.title, activity_pub_model.name)
        self.assertEqual(activity.description.html, activity_pub_model.summary)
        self.assertEqual(activity.slots.count(), activity_pub_model.sub_event.count())

    def test_url_field_included_when_set(self):
        """Test that url field is included in serialized output when it's set."""
        do_good_event = self.activity_pub_factory.create(
            url='https://example.com/activity'
        )
        serializer = self.activity_pub_serializer(
            instance=do_good_event, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertEqual(data['url'], 'https://example.com/activity')

    def test_url_field_included_when_none(self):
        """Test that url field is included in serialized output even when it's None."""
        do_good_event = self.activity_pub_factory.create(url=None)
        serializer = self.activity_pub_serializer(
            instance=do_good_event, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertIsNone(data['url'])


class GoodDeedSerializerTest(BluebottleTestCase):
    serializer_class = GoodDeedSerializer

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()
        return {'request': request}

    def test_url_field_included_when_set(self):
        """Test that url field is included in GoodDeedSerializer when it's set."""
        good_deed = GoodDeed.objects.create(
            name='Test Good Deed',
            summary='Test summary',
            url='https://example.com/good-deed'
        )

        serializer = self.serializer_class(
            instance=good_deed, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertEqual(data['url'], 'https://example.com/good-deed')

    def test_url_field_included_when_none(self):
        """Test that url field is included in GoodDeedSerializer even when it's None."""
        good_deed = GoodDeed.objects.create(
            name='Test Good Deed',
            summary='Test summary',
            url=None
        )

        serializer = self.serializer_class(
            instance=good_deed, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertIsNone(data['url'])


class CrowdFundingSerializerTest(BluebottleTestCase):
    serializer_class = CrowdFundingSerializer

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()
        return {'request': request}

    def test_url_field_included_when_set(self):
        """Test that url field is included in CrowdFundingSerializer when it's set."""
        crowd_funding = CrowdFunding.objects.create(
            name='Test Crowd Funding',
            summary='Test summary',
            url='https://example.com/crowd-funding',
            target=1000.00,
            target_currency='EUR'
        )

        serializer = self.serializer_class(
            instance=crowd_funding, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertEqual(data['url'], 'https://example.com/crowd-funding')

    def test_url_field_included_when_none(self):
        """Test that url field is included in CrowdFundingSerializer even when it's None."""
        crowd_funding = CrowdFunding.objects.create(
            name='Test Crowd Funding',
            summary='Test summary',
            url=None,
            target=1000.00,
            target_currency='EUR'
        )

        serializer = self.serializer_class(
            instance=crowd_funding, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertIsNone(data['url'])


class GrantApplicationSerializerTest(BluebottleTestCase):
    serializer_class = GrantApplicationSerializer

    @property
    def context(self):
        request = RequestFactory().get('/')
        request.user = BlueBottleUserFactory.create()
        return {'request': request}

    def test_url_field_included_when_set(self):
        """Test that url field is included in GrantApplicationSerializer when it's set."""
        grant_application = GrantApplication.objects.create(
            name='Test Grant Application',
            summary='Test summary',
            url='https://example.com/grant-application',
            target=1000.00,
            target_currency='EUR'
        )

        serializer = self.serializer_class(
            instance=grant_application, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertEqual(data['url'], 'https://example.com/grant-application')

    def test_url_field_included_when_none(self):
        """Test that url field is included in GrantApplicationSerializer even when it's None."""
        grant_application = GrantApplication.objects.create(
            name='Test Grant Application',
            summary='Test summary',
            url=None,
            target=1000.00,
            target_currency='EUR'
        )

        serializer = self.serializer_class(
            instance=grant_application, context=self.context
        )
        data = serializer.data

        self.assertIn('url', data)
        self.assertIsNone(data['url'])
