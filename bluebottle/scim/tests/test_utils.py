from django.test import TestCase
from bluebottle.scim.utils import SCIMPath


class ScimPathTestCase(TestCase):
    def setUp(self):
        super().setUp()

    def test_get(self):
        path = SCIMPath('title')
        self.assertEqual(
            path.get({'title': 'Developer'}),
            'Developer'
        )

    def test_get_dotted(self):
        path = SCIMPath('name.first')
        self.assertEqual(
            path.get({'name': {'first': 'Ernst', 'last': 'Odolphi'}}),
            'Ernst'
        )

    def test_get_dotted_deeper(self):
        path = SCIMPath('foo.bar.bla')
        self.assertEqual(
            path.get({'foo': {'bar': {'bla': 'bli'}}}),
            'bli'
        )

    def test_get_filter(self):
        path = SCIMPath('email[type eq "work"].value')
        self.assertEqual(
            path.get({
                'email': [
                    {'type': 'work', 'value': 'work@example.com'},
                    {'type': 'private', 'value': 'private@example.com'},
                ]
            }),
            'work@example.com'
        )

    def test_get_filter_other(self):
        path = SCIMPath('email[type eq "private"].value')
        self.assertEqual(
            path.get({
                'email': [
                    {'type': 'work', 'value': 'work@example.com'},
                    {'type': 'private', 'value': 'private@example.com'},
                ]
            }),
            'private@example.com'
        )

    def test_set(self):
        path = SCIMPath('title')
        data = {}
        path.set(data, 'Developer'),
        self.assertEqual(
            data,
            {'title': 'Developer'}
        )

    def test_set_dotted(self):
        path = SCIMPath('name.first')
        data = {}
        path.set(data, 'Ernst'),

        self.assertEqual(
            data,
            {'name': {'first': 'Ernst'}}
        )

    def test_set_dotted_existing_key(self):
        path = SCIMPath('name.first')
        data = {'name': {'last': 'Odolphi'}}
        path.set(data, 'Ernst'),

        self.assertEqual(
            data,
            {'name': {'first': 'Ernst', 'last': 'Odolphi'}}
        )

    def test_set_filter(self):
        path = SCIMPath('email[type eq "work"].value')
        data = {}
        path.set(data, 'work@example.com'),

        self.assertEqual(
            data,
            {'email': [{'type': 'work', 'value': 'work@example.com'}]}
        )

    def test_set_existing_filter(self):
        path = SCIMPath('email[type eq "work"].value')
        data = {'email': [{'type': 'private', 'value': 'private@example.com'}]}

        path.set(data, 'work@example.com'),

        self.assertEqual(
            data,
            {
                'email': [
                    {'type': 'private', 'value': 'private@example.com'},
                    {'type': 'work', 'value': 'work@example.com'}
                ]
            }
        )
