# coding=utf-8
from builtins import str
import json

from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from rest_framework import status

from bluebottle.impact.models import ImpactGoal
from bluebottle.impact.tests.factories import (
    ImpactTypeFactory, ImpactGoalFactory
)
from bluebottle.time_based.tests.factories import DateActivityFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class ImpactTypeListAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(ImpactTypeListAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.types = ImpactTypeFactory.create_batch(10)
        self.url = reverse('impact-type-list')
        self.user = BlueBottleUserFactory()

    def test_get(self):
        response = self.client.get(self.url, user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), len(self.types))

        resource = response.json()['data'][0]['attributes']

        self.assertTrue('slug' in resource)
        self.assertTrue('name' in resource)
        self.assertTrue('unit' in resource)
        self.assertTrue('text' in resource)
        self.assertTrue('text-with-target' in resource)
        self.assertTrue('text-passed' in resource)

        resource_type = response.json()['data'][0]['type']

        self.assertEqual(resource_type, 'activities/impact-types')

    def test_get_anonymous(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), len(self.types))

    def test_get_only_active(self):
        self.types[0].active = False
        self.types[0].save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), len(self.types) - 1)

    def test_get_closed(self):
        MemberPlatformSettings.objects.update(closed=True)

        response = self.client.get(self.url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_closed_anonymous(self):
        MemberPlatformSettings.objects.update(closed=True)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post(self):
        response = self.client.post(self.url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ImpactGoalListAPITestCase(BluebottleTestCase):
    def setUp(self):
        super(ImpactGoalListAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.activity = DateActivityFactory.create()
        self.type = ImpactTypeFactory.create()
        self.url = reverse('impact-goal-list')

        self.data = {
            'data': {
                'type': 'activities/impact-goals',
                'attributes': {
                    'target': 1.5
                },
                'relationships': {
                    'activity': {
                        'data': {
                            'type': 'activities/time-based/dates',
                            'id': self.activity.pk
                        },
                    },
                    'impact-type': {
                        'data': {
                            'type': 'activities/impact-types',
                            'id': self.type.pk
                        },
                    }

                }
            }
        }

    def test_create(self):
        response = self.client.post(
            self.url,
            json.dumps(self.data),
            user=self.activity.owner
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        resource_type = response.json()['data']['type']
        self.assertEqual(resource_type, 'activities/impact-goals')

        goal = ImpactGoal.objects.get(pk=response.json()['data']['id'])
        self.assertEqual(
            goal.target, self.data['data']['attributes']['target']
        )
        self.assertEqual(goal.type, self.type)
        self.assertEqual(goal.activity, self.activity)

    def test_create_no_target(self):
        del self.data['data']['attributes']['target']

        response = self.client.post(
            self.url,
            json.dumps(self.data),
            user=self.activity.owner
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        resource_type = response.json()['data']['type']
        self.assertEqual(resource_type, 'activities/impact-goals')

        goal = ImpactGoal.objects.get(pk=response.json()['data']['id'])
        self.assertEqual(
            goal.target, None
        )
        self.assertEqual(goal.type, self.type)
        self.assertEqual(goal.activity, self.activity)

    def test_create_non_owner(self):
        response = self.client.post(
            self.url,
            json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_anonymous(self):
        response = self.client.post(
            self.url,
            json.dumps(self.data),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ImpactGoalDetailsAPITestCase(BluebottleTestCase):
    def setUp(self):
        super(ImpactGoalDetailsAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.activity = DateActivityFactory.create()
        self.type = ImpactTypeFactory.create()
        self.goal = ImpactGoalFactory(type=self.type, activity=self.activity)
        self.url = reverse('impact-goal-details', args=(self.goal.pk, ))

        self.data = {
            'data': {
                'type': 'activities/impact-goals',
                'id': self.goal.pk,
                'attributes': {
                    'target': 1.5
                },
            }
        }

    def test_get(self):
        response = self.client.get(
            self.url,
            user=self.activity.owner
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()['data']

        self.assertEqual(data['type'], 'activities/impact-goals')

        self.assertEqual(
            data['attributes']['target'], self.goal.target
        )
        self.assertEqual(
            data['relationships']['impact-type']['data']['id'],
            str(self.goal.type.pk)
        )
        self.assertEqual(
            data['relationships']['activity']['data']['id'],
            str(self.goal.activity.pk)
        )

    def test_get_incomplete(self):
        self.goal.target = None
        self.goal.save()

        response = self.client.get(
            self.url,
            user=self.activity.owner
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()['data']
        self.assertEqual(data['meta']['required'], [])

    def test_get_non_owner(self):
        response = self.client.get(
            self.url,
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_closed_anonymous(self):
        anonymous = Group.objects.get(name='Anonymous')
        anonymous.permissions.remove(
            Permission.objects.get(codename='api_read_dateactivity')
        )

        MemberPlatformSettings.objects.update(closed=True)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update(self):
        response = self.client.patch(
            self.url,
            data=json.dumps(self.data),
            user=self.activity.owner
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()['data']

        self.assertEqual(data['type'], 'activities/impact-goals')

        self.assertEqual(
            data['attributes']['target'],
            self.data['data']['attributes']['target']
        )

        self.goal.refresh_from_db()
        self.assertEqual(
            self.goal.target,
            self.data['data']['attributes']['target']
        )

    def test_update_other_user(self):
        response = self.client.patch(
            self.url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_anonymous(self):
        response = self.client.patch(
            self.url,
            data=json.dumps(self.data)
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete(self):
        response = self.client.delete(
            self.url,
            user=self.activity.owner
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(ImpactGoal.DoesNotExist):
            ImpactGoal.objects.get(pk=self.goal.pk)

    def test_delete_other_user(self):
        response = self.client.delete(
            self.url,
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_anonymous(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
