from datetime import datetime
from urllib.parse import urlparse
from operator import attrgetter
from io import BytesIO

import httmock
from django.test import RequestFactory
from django.utils.timezone import get_current_timezone
from requests import Response

from bluebottle.cms.models import SitePlatformSettings

from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.models import (
    ActivityPubModel, Inbox, Outbox, PublicKey
)
from bluebottle.activity_pub.serializers.base import ActivityPubSerializer
from bluebottle.activity_pub.tests.factories import (
    DoGoodEventFactory, OrganizationFactory, FollowFactory, GoodDeedFactory,
    CrowdFundingFactory
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


renderer = JSONLDRenderer()


class JSONLDSerializerTestCase:
    mocks = []

    def setUp(self):
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

        for field in self.fields:
            expected = attrgetter(field)(self.instance)
            if isinstance(expected, ActivityPubModel):
                item = representation[field]

                if isinstance(item, dict):
                    item = item['id']

                self.assertEqual(
                    item,
                    expected.pub_url
                )
            else:
                if isinstance(expected, datetime):
                    expected = expected.astimezone(get_current_timezone()).isoformat()

                self.assertEqual(
                    representation[field],
                    expected
                )

    def test_create(self):
        with httmock.HTTMock(*self.mocks):
            serializer = ActivityPubSerializer(data=self.data, context=self.context)

            self.assertTrue(serializer.is_valid())

        self.instance = serializer.save()
        self.check(serializer)

    def check(self, serializer):
        for field in self.fields:
            expected = attrgetter(field)(self.instance)
            data = serializer.initial_data[field]
            if isinstance(expected, ActivityPubModel):
                expected = expected.pub_url
                if isinstance(data, dict) and 'id' in data:
                    data = data['id']

            if isinstance(expected, datetime):
                expected = expected.astimezone(get_current_timezone()).isoformat()

            self.assertEqual(data, expected)

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
    fields = ['name', 'content', 'summary', 'outbox', 'inbox']

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


def mock_resource(model):
    @httmock.urlmatch(method="GET", path=urlparse(model.iri).path)
    def mocked_resource(url, request):
        data = ActivityPubSerializer(instance=model).data

        return {
            'content': renderer.render(data),
            'status_code': 200,
            'headers': {'content-type': 'application/ld+json'}
        }

    return mocked_resource


class FollowSerializerTestCase(JSONLDSerializerTestCase, BluebottleTestCase):
    factory = FollowFactory
    fields = ['actor', 'object', 'adoption_type']

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
        return [mock_resource(model) for model in [self.actor, self.object, self.next_object]]

    def update(self):
        self.data['object'] = self.next_object.iri


class DoGoodEventSerializerTestCase(JSONLDSerializerTestCase, BluebottleTestCase):
    factory = DoGoodEventFactory
    fields = ['name', 'summary', 'start_time', 'end_time', 'image']

    def setUp(self):
        super().setUp()

        self.data = {
            'application_deadline': None,
            'duration': None,
            'end_time': None,
            'event_attendance_mode': None,
            'id': 'http://example.com/api/json-ld/do-good-event/1',
            'image': {
                'id': 'http://example.com/api/json-ld/image/1',
                'name': None,
                'url': 'https://dummyimage.com/352x72'
            },
            'join_mode': None,
            'location': None,
            'name': 'Character above memory.',
            'organization': {
                'content': 'Organization content',
                'icon': None,
                'id': 'http://example.com/api/json-ld/organization/1',
                'image': {
                    'id': 'http://example.com/api/json-ld/image/2',
                    'name': None,
                    'url': 'https://dummyimage.com/529x447'
                },
                'inbox': 'http://example.com/api/json-ld/inbox/1',
                'name': 'Organization name',
                'outbox': 'http://example.com/api/json-ld/outbox/1',
                'public_key': {
                    'id': 'http://example.com/api/json-ld/public-key/1',
                    'public_key_pem': 'public-key'
                },
                'summary': 'Organization summart'
            },
            'repetition_mode': None,
            'slot_mode': 'SetSlotMode',
            'start_time': None,
            'sub_event': [],
            'summary': 'summary',
            'type': 'DoGoodEvent',
            'url': 'http://example.com/activities/1'
        }

    def update(self):
        self.data['name'] = 'Some name'


class GoodDeedSerializerTest(JSONLDSerializerTestCase, BluebottleTestCase):
    factory = GoodDeedFactory
    fields = ['name', 'summary', 'start_time', 'end_time', 'image']

    def setUp(self):
        super().setUp()

        self.data = {
            'type': 'GoodDeed',
            'id': 'http://example.com/api/json-ld/good-deed/1',
            'name': 'Idea election.',
            'summary': 'Some summary',
            'image': {
                'id': 'http://example.com/api/json-ld/image/1',
                'url': 'https://placeimg.com/733/689/any',
                'name': None
            },
            'organization': {
                'id': 'http://example.com/api/json-ld/organization/1',
                'inbox': 'http://example.com/api/json-ld/inbox/1',
                'outbox': 'http://example.com/api/json-ld/outbox/1',
                'public_key': {
                    'id': 'http://example.com/api/json-ld/public-key/1',
                    'public_key_pem': 'public-key'
                },
                'name': 'ActivityPub Organization 0',
                'summary': 'Organization summarty',
                'content': 'Organization content',
                'image': {
                    'id': 'http://example.com/api/json-ld/image/2',
                    'url': 'https://picsum.photos/536/199',
                    'name': None
                },
                'icon': None},
            'url': 'http://example.com/activities/1',
            'start_time': '2026-04-24T10:45:28.569851+02:00',
            'end_time': '2026-04-25T10:45:28.569869+02:00'
        }

    def update(self):
        self.data['name'] = 'Some name'


class CrowdFundingSerializerTest(JSONLDSerializerTestCase, BluebottleTestCase):
    factory = CrowdFundingFactory

    fields = ['name', 'summary', 'start_time', 'end_time', 'image']

    def setUp(self):
        super().setUp()

        self.data = {
            'donated': '2000.00',
            'donated_currency': 'EUR',
            'end_time': '2026-04-25T11:36:12.151791+02:00',
            'id': 'http://example.com/api/json-ld/crowd-funding/1',
            'image': {
                'id': 'http://example.com/api/json-ld/image/1',
                'name': None,
                'url': 'https://placeimg.com/743/766/any'
            },
            'location': None,
            'name': 'name',
            'organization': {
                'content': 'content',
                'icon': None,
                'id': 'http://example.com/api/json-ld/organization/1',
                'image': {
                    'id': 'http://example.com/api/json-ld/image/1',
                    'name': None,
                    'url': 'https://placekitten.com/337/220'
                },
                'inbox': 'http://example.com/api/json-ld/inbox/1',
                'name': 'ActivityPub Organization 0',
                'outbox': 'http://example.com/api/json-ld/outbox/1',
                'public_key': {
                    'id': 'http://example.com/api/json-ld/public-key/1',
                    'public_key_pem': 'public-key',
                },
                'summary': 'summary'
            },
            'start_time': '2026-04-24T11:36:12.151754+02:00',
            'summary': 'Later add kid. Pull wrong effort minute.',
            'target': '5000.00',
            'target_currency': 'EUR',
            'type': 'CrowdFunding',
            'url': 'http://exampe.com/activities/1'
        }

    def update(self):
        self.data['name'] = 'Some name'
