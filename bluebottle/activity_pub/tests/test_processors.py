import datetime

from bluebottle.activity_pub.parsers import default_context, processor
from bluebottle.test.utils import BluebottleTestCase


class JSONLDProcessorTestCase(BluebottleTestCase):
    def expand(self, data):
        return processor.expand(data, {})[0]

    def test_expand_person(self):
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
        result = self.expand(data)
        attributes = {
            '@id',
            '@type',
            'http://www.w3.org/ns/ldp#inbox',
            'https://www.w3.org/ns/activitystreams#name',
            'https://www.w3.org/ns/activitystreams#outbox',
            'https://w3id.org/security#publicKey',
        }
        self.assertEqual(attributes, set(result.keys()))

    def test_expand_follow(self):
        data = {
            '@context': default_context,
            'id': 'https://example.com/follow',
            'object': 'https://example.com/object',
            'actor': 'https://example.com/actor',
            'type': 'Follow'
        }
        result = self.expand(data)
        attributes = {
            '@id',
            '@type',
            'https://www.w3.org/ns/activitystreams#actor',
            'https://www.w3.org/ns/activitystreams#object'
        }
        self.assertEqual(attributes, set(result.keys()))
        self.assertEqual(result['@type'], ['https://www.w3.org/ns/activitystreams#Follow'])

    def test_parse_follow_prefixed(self):
        data = {
            '@context': default_context,
            'id': 'https://example.com/follow',
            'as:object': {'@id': 'https://example.com/object'},
            'as:actor': {'@id': 'https://example.com/actor'},
            'type': 'as:Follow',
        }
        result = self.expand(data)
        attributes = {
            '@id',
            '@type',
            'https://www.w3.org/ns/activitystreams#actor',
            'https://www.w3.org/ns/activitystreams#object'
        }
        self.assertEqual(attributes, set(result.keys()))

    def test_expand_deed(self):
        data = {
            '@context': default_context,
            'id': 'https://example.com/deed',
            'name': 'Activity title',
            'summary': 'Some activity description',
            'startTime': datetime.date(2026, 1, 1).isoformat(),
            'endTime': datetime.date(2026, 2, 1).isoformat(),
            'type': 'GoodDeed',
        }
        result = self.expand(data)
        attributes = {
            '@id',
            '@type',
            'https://www.w3.org/ns/activitystreams#name',
            'https://www.w3.org/ns/activitystreams#summary',
            'https://www.w3.org/ns/activitystreams#startTime',
            'https://www.w3.org/ns/activitystreams#endTime',
        }
        self.assertEqual(attributes, set(result.keys()))

        self.assertEqual(result['@type'], ['https://goodup.com/json-ld#GoodDeed'])

    def test_expand_funding(self):
        data = {
            '@context': default_context,
            'id': 'https://example.com/funding',
            'name': 'Activity title',
            'summary': 'Some activity description',
            'startTime': datetime.date(2026, 1, 1).isoformat(),
            'endTime': datetime.date(2026, 2, 1).isoformat(),
            'target': 1000,
            'targetCurrency': 'eur',
            'type': 'CrowdFunding',
        }
        result = self.expand(data)
        attributes = {
            '@id',
            '@type',
            'https://www.w3.org/ns/activitystreams#name',
            'https://www.w3.org/ns/activitystreams#summary',
            'https://www.w3.org/ns/activitystreams#startTime',
            'https://www.w3.org/ns/activitystreams#endTime',
            'https://goodup.com/json-ld#target',
            'https://goodup.com/json-ld#targetCurrency',
        }
        self.assertEqual(attributes, set(result.keys()))

        self.assertEqual(result['@type'], ['https://goodup.com/json-ld#CrowdFunding'])

    def test_expand_date_activity(self):
        data = {
            '@context': default_context,
            'id': 'https://example.com/date',
            'name': 'Activity title',
            'summary': 'Some activity description',
            'subEvent': [{
                'id': 'https://example.com/slot',
                'startTime': datetime.date(2026, 1, 1).isoformat(),
                'endTime': datetime.date(2026, 2, 1).isoformat(),
                'location': {
                    'id': 'https://example.com/slot',
                    'latitude': 20.45,
                    'longitude': 40.3,
                    'address': {
                        'id': 'https://example.com/address',
                        'locality': 'Amsterdam',
                        'country': 'NL',
                        'postalCode': '1013BZ',
                        'streetAddress': 'Van Noordtkade 24b'
                    }
                },
            }],
            'type': 'Event',
        }
        result = self.expand(data)

        self.assertEqual(result['@type'], ['https://www.w3.org/ns/activitystreams#Event'])
        attributes = {
            '@id',
            '@type',
            'https://www.w3.org/ns/activitystreams#name',
            'https://www.w3.org/ns/activitystreams#summary',
            'https://goodup.com/json-ld#subEvent',
        }
        self.assertEqual(attributes, set(result.keys()))

        sub_event_attributes = {
            '@id',
            'https://www.w3.org/ns/activitystreams#location',
            'https://www.w3.org/ns/activitystreams#startTime',
            'https://www.w3.org/ns/activitystreams#endTime',

        }
        sub_event = result['https://goodup.com/json-ld#subEvent'][0]
        self.assertEqual(
            sub_event_attributes, set(sub_event.keys())
        )

        location_attributes = {
            '@id',
            'https://www.w3.org/ns/activitystreams#longitude',
            'https://www.w3.org/ns/activitystreams#latitude',
            'https://www.w3.org/ns/activitystreams#address',

        }
        location = sub_event['https://www.w3.org/ns/activitystreams#location'][0]
        self.assertEqual(
            location_attributes,
            set(location.keys())
        )

        address_attributes = {
            '@id',
            'https://schema.org/addressLocality',
            'https://schema.org/addressCountry',
            'https://schema.org/postalCode',
            'https://schema.org/streetAddress'
        }
        address = location['https://www.w3.org/ns/activitystreams#address'][0]
        self.assertEqual(
            address_attributes,
            set(address.keys())
        )
