import pickle
from io import BytesIO
from unittest import mock

from django.db import connection
from django.test import TestCase, override_settings
from kombu.exceptions import EncodeError

from bluebottle.activity_pub.adapters import JSONLDAdapter, publish_to_recipient
from bluebottle.activity_pub.models import Inbox
from bluebottle.activity_pub.tests.factories import FollowFactory
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.test.factory_models.organizations import (
    OrganizationFactory as BluebottleOrganizationFactory
)
from bluebottle.test.utils import BluebottleTestCase


class JSONLDAdapterTestCase(TestCase):
    def setUp(self):
        self.adapter = JSONLDAdapter()

    def test_do_request_raises_for_local_url(self):
        with mock.patch('bluebottle.activity_pub.adapters.is_local', return_value=True):
            with self.assertRaises(TypeError):
                self.adapter.do_request('get', 'http://test.localhost/resource')

    @mock.patch('bluebottle.activity_pub.adapters.requests.get')
    def test_get_parses_json_ld_response(self, mock_get):
        mock_response = mock.Mock()
        mock_response.content = b'{"@context": "https://www.w3.org/ns/activitystreams"}'
        mock_response.headers = {'content-type': 'application/ld+json'}
        mock_response.raise_for_status = mock.Mock()
        mock_get.return_value = mock_response
        parsed = {'@context': 'https://www.w3.org/ns/activitystreams'}

        with mock.patch('bluebottle.activity_pub.adapters.is_local', return_value=False):
            with mock.patch.object(self.adapter.parser, 'parse', return_value=parsed) as parse:
                result = self.adapter.get('https://remote.example/object')

        self.assertEqual(result, parsed)
        parse.assert_called_once()
        stream, media_type = parse.call_args[0]
        self.assertIsInstance(stream, BytesIO)
        self.assertEqual(media_type, 'application/ld+json')

    @mock.patch('bluebottle.activity_pub.adapters.requests.get')
    def test_execute_raises_when_request_fails(self, mock_get):
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = Exception('error')
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            self.adapter.execute('get', 'https://remote.example/resource')


@override_settings(TESTING=False, CELERY_ALWAYS_EAGER=False)
class PublishRecipientTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        SitePlatformSettings.objects.create(
            organization=BluebottleOrganizationFactory.create()
        )

    def create_follow(self):
        return FollowFactory.create(actor=None)

    def test_task_gets_primitive_arguments(self):
        with mock.patch('bluebottle.activity_pub.adapters.publish_to_recipient.delay') as delay:
            follow = self.create_follow()

        recipient = follow.recipients.get()
        delay.assert_called_once_with(recipient.pk, connection.tenant.schema_name)
        pickle.dumps(delay.call_args)

    def test_queue_failure_does_not_fail_save(self):
        with mock.patch(
            'bluebottle.activity_pub.adapters.publish_to_recipient.delay',
            side_effect=EncodeError("Can't pickle QuerySet.distinct")
        ):
            with mock.patch('bluebottle.activity_pub.adapters.logger') as logger:
                follow = self.create_follow()

        logger.exception.assert_called_once()
        self.assertEqual(follow.recipients.count(), 1)

    def test_task_publishes_recipient(self):
        with mock.patch('bluebottle.activity_pub.adapters.publish_to_recipient.delay'):
            follow = self.create_follow()

        recipient = follow.recipients.get()
        Inbox.objects.filter(pk=recipient.actor.inbox_id).update(iri='https://example.com/inbox')

        with mock.patch.object(JSONLDAdapter, 'post') as post:
            publish_to_recipient(recipient.pk, connection.tenant.schema_name)

        post.assert_called_once()
        recipient.refresh_from_db()
        self.assertTrue(recipient.send)
