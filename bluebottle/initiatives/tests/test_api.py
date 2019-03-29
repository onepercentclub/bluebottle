import json

from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status
from django.test import Client

from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.tests.factories import InitiativeFactory, ThemeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class JSONAPITestClient(Client):
    def patch(self, path, data='', content_type='application/vnd.api+json', follow=False, secure=False, **extra):
        return super(JSONAPITestClient, self).put(path, data, content_type, follow, secure, **extra)

    def post(self, path, data='', content_type='application/vnd.api+json', follow=False, secure=False, **extra):
        return super(JSONAPITestClient, self).post(path, data, content_type, follow, secure, **extra)


    def generic(self, method, path, data='', content_type='application/vnd.api+json', secure=False, user=None, **extra):
        if user:
            extra['HTTP_AUTHORIZATION'] ="JWT {0}".format(user.get_jwt_token())

        return super(JSONAPITestClient, self).generic(method, path, data, content_type, secure, **extra)



class InitiativeAPITestCase(TestCase):
    """
    Integration tests for the Categories API.
    """

    def setUp(self):
        super(InitiativeAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory.create()


class InitiativeListAPITestCase(InitiativeAPITestCase):
    def setUp(self):
        super(InitiativeListAPITestCase, self).setUp()
        self.theme = ThemeFactory.create()
        self.url = reverse('initiative-list')

    def test_create(self):
        data = {
            'data': {
                'type': 'Initiative',
                'attributes': {
                    'title': 'Some title'
                },
                'relationships': {
                    'theme': {
                        'data': {
                            'type': 'Theme', 'id': self.theme.pk
                        },
                    },
                }
            }
        }
        response = self.client.post(
            '{}?{}'.format(self.url, 'include=owner,reviewer,theme'),
            json.dumps(data),
            user=self.owner
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)

        initiative = Initiative.objects.get(pk=data['data']['id'])

        self.assertEqual(data['data']['attributes']['title'], initiative.title)
        self.assertEqual(
            data['data']['relationships']['owner']['data']['id'],
            unicode(self.owner.pk)
        )
        self.assertEqual(
            data['data']['relationships']['theme']['data']['id'],
            unicode(initiative.theme.pk)
        )
        self.assertEqual(len(data['included']), 2)

    def test_create_anonymous(self):
        response = self.client.post(
            '{}?{}'.format(self.url, 'include=owner,reviewer,theme'),
            json.dumps({})
        )
        self.assertEqual(response.status_code, 401)


class InitiativeDetailAPITestCase(InitiativeAPITestCase):
    def setUp(self):
        super(InitiativeDetailAPITestCase, self).setUp()
        self.initiative = InitiativeFactory(
            owner=self.owner
        )

        self.url = reverse('initiative-detail', args=(self.initiative.pk, ))

    def test_patch(self):
        data = {
            'data': {
                'id': self.initiative.id,
                'type': 'Initiative',
                'attributes': {
                    'title': 'Some title'
                }
            }
        }
        response = self.client.patch(
            '{}?{}'.format(self.url, 'include=owner,reviewer,theme'),
            json.dumps(data),
            user=self.owner
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['data']['attributes']['title'], 'Some title')

<<<<<<< HEAD
    def test_put_image(self):
        file_path = './bluebottle/files/tests/files/test-image.png'
        with open(file_path) as test_file:
            response = self.client.post(
                reverse('file-list'),
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="filename.jpg"',
                HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
            )

        file_data = json.loads(response.content)

        data = {
            'data': {
                'id': self.initiative.id,
                'type': 'Initiative',
                'relationships': {
                    'image': {
                        'data': {
                            'type': 'File',
                            'id': file_data['data']['id']
                          }
                    }
                }
            }
        }
        response = self.client.patch(
            '{}?{}'.format(self.url, 'include=owner,reviewer,theme'),
            json.dumps(data),
            content_type="application/vnd.api+json",
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(
            data['data']['relationships']['image']['data']['id'],
            file_data['data']['id']
        )

        response = self.client.get(
            data['data']['relationships']['image']['links']['200x300'],
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        self.assertTrue(
            response['X-Accel-Redirect'].startswith(
                '/media/cache/'
            )
        )
=======
    def test_patch_anonymous(self):
        response = self.client.patch(
            '{}?{}'.format(self.url, 'include=owner,reviewer,theme'),
            json.dumps({}),
        )
        self.assertEqual(response.status_code, 401)

    def test_patch_wrong_user(self):
        response = self.client.patch(
            '{}?{}'.format(self.url, 'include=owner,reviewer,theme'),
            json.dumps({}),
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, 403)
>>>>>>> feature/initiatives

    def test_get(self):
        response = self.client.get('{}?{}'.format(self.url, 'include=owner,reviewer,theme'))
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(data['data']['attributes']['title'], self.initiative.title)
        self.assertEqual(data['data']['relationships']['theme']['data']['id'], unicode(self.initiative.theme.pk))
        self.assertEqual(data['data']['relationships']['owner']['data']['id'], unicode(self.initiative.owner.pk))
        self.assertEqual(len(data['included']), 3)
