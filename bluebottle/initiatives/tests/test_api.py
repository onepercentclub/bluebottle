import json

from django.core.urlresolvers import reverse
from django.test import TestCase

from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectThemeFactory
from bluebottle.test.utils import JSONAPITestClient


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
        self.theme = ProjectThemeFactory.create()
        self.url = reverse('initiative-list')

    def test_create(self):
        data = {
            'data': {
                'type': 'initiatives',
                'attributes': {
                    'title': 'Some title'
                },
                'relationships': {
                    'theme': {
                        'data': {
                            'type': 'themes', 'id': self.theme.pk
                        },
                    },
                }
            }
        }
        response = self.client.post(
            self.url,
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
            self.url,
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
                'type': 'initiatives',
                'attributes': {
                    'title': 'Some title'
                }
            }
        }
        response = self.client.patch(
            self.url,
            json.dumps(data),
            user=self.owner
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['data']['attributes']['title'], 'Some title')

    def test_put_image(self):
        file_path = './bluebottle/files/tests/files/test-image.png'
        with open(file_path) as test_file:
            response = self.client.post(
                reverse('file-list'),
                test_file.read(),
                content_type="image/jpg",
                HTTP_CONTENT_DISPOSITION='attachment; filename="some_file.jpg"',
                HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
            )

        file_data = json.loads(response.content)
        data = {
            'data': {
                'id': self.initiative.id,
                'type': 'initiatives',
                'relationships': {
                    'image': {
                        'data': {
                            'type': 'files',
                            'id': file_data['data']['id']
                        }
                    }
                }
            }
        }
        response = self.client.patch(
            self.url,
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
            data['included'][0]['attributes']['links']['large'],
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        self.assertTrue(
            response['X-Accel-Redirect'].startswith(
                '/media/cache/'
            )
        )

    def test_patch_anonymous(self):
        data = {
            'data': {
                'id': self.initiative.id,
                'type': 'initiatives',
                'attributes': {
                    'title': 'Some title'
                }
            }
        }

        response = self.client.patch(
            self.url,
            json.dumps(data),
        )
        self.assertEqual(response.status_code, 401)

    def test_patch_wrong_user(self):
        data = {
            'data': {
                'id': self.initiative.id,
                'type': 'initiatives',
                'attributes': {
                    'title': 'Some title'
                }
            }
        }

        response = self.client.patch(
            self.url,
            json.dumps(data),
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(data['data']['attributes']['title'], self.initiative.title)
        self.assertEqual(data['data']['relationships']['theme']['data']['id'], unicode(self.initiative.theme.pk))
        self.assertEqual(data['data']['relationships']['owner']['data']['id'], unicode(self.initiative.owner.pk))
        self.assertEqual(len(data['included']), 3)


class InitiativeListFilterAPITestCase(InitiativeAPITestCase):
    def setUp(self):
        super(InitiativeListFilterAPITestCase, self).setUp()
        self.url = reverse('initiative-list')

    def test_no_filter(self):
        InitiativeFactory.create(owner=self.owner)
        InitiativeFactory.create()

        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)

    def test_filter_owner(self):
        InitiativeFactory.create(owner=self.owner)
        InitiativeFactory.create()

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['relationships']['owner']['data']['id'], unicode(self.owner.pk))
