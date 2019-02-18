import json

from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status

from bluebottle.initiatives.tests.factories import InitiativeFactory, ThemeFactory
from bluebottle.initiatives.models import Initiative
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class TransitionListAPITestCase(TestCase):
    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.initiative = InitiativeFactory(
            owner=self.owner
        )
        self.url = reverse('transition-list')

        super(TransitionListAPITestCase, self).setUp()

    def test_transition_to_submitted(self):
        data = {
            'data': {
                'type': 'Transition',
                'attributes': {
                    'transition': 'submit',
                    'field': 'review_status',
                },
                'relationships': {
                    'resource': {
                        'data': {
                            'type': 'Iniative',
                            'id': self.initiative.pk
                        }
                    }
                }
            }
        }

        response = self.client.post(
            self.url,
            json.dumps(data),
            content_type="application/vnd.api+json",
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        self.assertEqual(response.status_code, 201)

        initiaitive = Initiative.objects.get(pk=self.initiative.pk)
        self.assertEqual(initiaitive.review_status, 'submitted')
        import ipdb; ipdb.set_trace()


class InitiativeAPITestCase(TestCase):
    """
    Integration tests for the Categories API.
    """

    def setUp(self):
        super(InitiativeAPITestCase, self).setUp()
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
            content_type="application/vnd.api+json",
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['title'], 'Some title')
        self.assertEqual(
            data['data']['relationships']['owner']['data']['id'],
            unicode(self.owner.pk)
        )
        self.assertEqual(
            data['data']['relationships']['theme']['data']['id'],
            unicode(self.theme.pk)
        )


class InitiativeDetailAPITestCase(InitiativeAPITestCase):
    def setUp(self):
        super(InitiativeDetailAPITestCase, self).setUp()
        self.initiative = InitiativeFactory(
            owner=self.owner
        )

        self.url = reverse('initiative-detail', args=(self.initiative.pk, ))

    def test_put(self):
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
            content_type="application/vnd.api+json",
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['data']['attributes']['title'], 'Some title')

    def test_get(self):
        response = self.client.get('{}?{}'.format(self.url, 'include=owner,reviewer,theme'))
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(data['data']['attributes']['title'], self.initiative.title)
