from io import BytesIO
import json

from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.test.utils import BluebottleTestCase


class ParserTestCase(BluebottleTestCase):
    parser_class = JSONLDParser

    def setUp(self):
        self.parser = self.parser_class()
        super().setUp()

    def parse(self, data):
        return self.parser.parse(BytesIO(json.dumps(data).encode('utf-8')))

    def test_parse_person(self):
        data = {
            '@context': ['https://www.w3.org/ns/activitystreams', 'https://w3id.org/security/v1'],
            'id': 'https://example.com/person',
            'inbox': 'https://example.com/person/inbox',
            'outbox': 'https://example.com/person/outbox',
            'name': 'Tester',
            'publicKey': {
                'id': 'https://example.com/person/public-key',
                'publicKeyPem': 'some-public-key'
            },
            'type': 'Person'
        }
        result = self.parse(data)

        for key in ['id', 'inbox', 'outbox', 'name', 'public_key', 'type']:
            self.assertTrue(key in result, f'{key} should be in {result}')

    def test_parse_follow(self):
        data = {
            '@context': ['https://www.w3.org/ns/activitystreams', 'https://w3id.org/security/v1'],
            'id': 'https://example.com/follow',
            'object': 'https://example.com/object',
            'actor': 'https://example.com/actor',
            'type': 'Follow'
        }
        result = self.parse(data)

        for key in ['object', 'actor', 'id', 'type']:
            self.assertTrue(key in result, f'{key} should be in {result}')
            self.assertTrue(isinstance(result[key], str))

    def test_parse_follow_prefixed(self):
        data = {
            '@context': ['https://www.w3.org/ns/activitystreams', 'https://w3id.org/security/v1'],
            'id': 'https://example.com/follow',
            'as:object': {'@id': 'https://example.com/object'},
            'as:actor': {'@id': 'https://example.com/actor'},
            'type': 'as:Follow',
        }
        result = self.parse(data)
        for key in ['object', 'actor', 'id', 'type']:
            self.assertTrue(key in result, f'{key} should be in {result}')
            self.assertTrue(isinstance(result[key], str))
