from io import BytesIO
from unittest import mock

from django.test import TestCase

from bluebottle.activity_pub.adapters import JSONLDAdapter


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
