import json
from datetime import timedelta

from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status

from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class AssignementAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(AssignementAPITestCase, self).setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=['assignment']
        )

        self.client = JSONAPITestClient()
        self.url = reverse('assignment-list')
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)

    def test_create_assignment(self):
        data = {
            'data': {
                'type': 'activities/assignments',
                'attributes': {
                    'title': 'Business plan Young Freddy',
                    'deadline': str((now() + timedelta(days=21)).date()),
                    'duration': 8,
                    'registration_deadline': str((now() + timedelta(days=14)).date()),
                    'capacity': 2,
                    'description': 'Help Young Freddy write a business plan'
                },
                'relationships': {
                    'initiative': {
                        'data': {
                            'type': 'initiatives', 'id': self.initiative.id
                        },
                    },
                }
            }
        }
        response = self.client.post(self.url, json.dumps(data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'in_review')
        self.assertEqual(response.data['title'], 'Business plan Young Freddy')
