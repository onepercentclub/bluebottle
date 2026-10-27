from unittest import mock

import requests
from django.test import TestCase

from bluebottle.webfinger.client import WebFingerClient


class WebFingerClientTestCase(TestCase):
    def test_get_returns_activity_json_self_link(self):
        client = WebFingerClient()
        response_payload = {
            'links': [
                {
                    'rel': 'self',
                    'type': 'application/activity+json',
                    'href': 'https://remote.example/actors/1',
                },
            ],
        }

        with mock.patch.object(client, '_do_request', return_value=response_payload):
            href = client.get('https://remote.example/user@remote.example')

        self.assertEqual(href, 'https://remote.example/actors/1')

    def test_get_retries_with_domain_on_http_error(self):
        client = WebFingerClient()
        response_payload = {
            'links': [
                {
                    'rel': 'self',
                    'type': 'application/activity+json',
                    'href': 'https://remote.example/actors/domain',
                },
            ],
        }

        with mock.patch.object(
            client,
            '_do_request',
            side_effect=[requests.HTTPError(), response_payload],
        ) as do_request:
            href = client.get('https://remote.example/user@remote.example')

        self.assertEqual(href, 'https://remote.example/actors/domain')
        self.assertEqual(do_request.call_count, 2)
