import json
from datetime import timedelta

from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status

from bluebottle.assignments.tests.factories import AssignmentFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient, get_included


class AssignmentCreateAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(AssignmentCreateAPITestCase, self).setUp()
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
                    'end_date': str((now() + timedelta(days=21)).date()),
                    'end_date_type': 'deadline',
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

    def test_create_event_missing_date(self):
        data = {
            'data': {
                'type': 'activities/assignments',
                'attributes': {
                    'title': '',
                    'end_date': str((now() + timedelta(days=21)).date()),
                    'registration_deadline': str((now() + timedelta(days=14)).date()),
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

        validations = get_included(response, 'activities/assignment-validations')

        self.assertEqual(
            validations['attributes']['title'][0]['title'],
            u'This field may not be blank.'
        )
        self.assertEqual(
            validations['attributes']['end-date-type'][0]['title'],
            u'This field may not be null.'
        )
        self.assertEqual(
            validations['attributes']['is-online'][0]['title'],
            u'This field may not be null.'
        )
        self.assertEqual(
            validations['attributes']['location'][0]['title'],
            u"This field is required or select 'Online'"
        )

    def test_create_registration_deadline(self):
        data = {
            'data': {
                'type': 'activities/assignments',
                'attributes': {
                    'title': '',
                    'end_date': str((now() + timedelta(days=21)).date()),
                    'registration_deadline': str((now() + timedelta(days=22)).date()),
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

        validations = get_included(response, 'activities/assignment-validations')

        self.assertEqual(
            validations['attributes']['registration-deadline'][0]['title'],
            u'Registration deadline should be before end date'
        )


class AssignmentDetailAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(AssignmentDetailAPITestCase, self).setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=['assignment']
        )

        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)
        self.assignment = AssignmentFactory.create(initiative=self.initiative)

        self.client = JSONAPITestClient()
        self.url = reverse('assignment-detail', args=(self.assignment.id,))

    def test_retrieve_assignment(self):
        response = self.client.get(self.url, user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_review')
