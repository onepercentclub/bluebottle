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

    def test_create_event_missing_data(self):
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


class AssignmentTransitionTestCase(BluebottleTestCase):

    def setUp(self):
        super(AssignmentTransitionTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory()
        self.manager = BlueBottleUserFactory()
        self.other_user = BlueBottleUserFactory()

        self.initiative = InitiativeFactory.create(activity_manager=self.manager)
        self.assignment_incomplete = AssignmentFactory.create(
            owner=self.owner,
            initiative=self.initiative
        )
        self.assignment = AssignmentFactory.create(
            owner=self.owner,
            initiative=self.initiative,
            is_online=True,
            duration=4,
            end_date_type='deadline',
            end_date=(now() + timedelta(weeks=2)).date()
        )

        self.assignment_incomplete_url = reverse('assignment-detail', args=(self.assignment_incomplete.id,))
        self.assignment_url = reverse('assignment-detail', args=(self.assignment.id,))
        self.transition_url = reverse('assignment-transition-list')
        self.review_transition_url = reverse('activity-review-transition-list')

        self.review_data = {
            'data': {
                'type': 'activities/review-transitions',
                'attributes': {
                    'transition': 'submit',
                },
                'relationships': {
                    'resource': {
                        'data': {
                            'type': 'activities/assignments',
                            'id': self.assignment.pk
                        }
                    }
                }
            }
        }
        self.transition_data = {
            'data': {
                'type': 'assignment-transitions',
                'attributes': {
                    'transition': 'close',
                },
                'relationships': {
                    'resource': {
                        'data': {
                            'type': 'activities/assignments',
                            'id': self.assignment.pk
                        }
                    }
                }
            }
        }

    def test_check_validations_missing_data(self):
        response = self.client.get(
            self.assignment_incomplete_url,
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        review_transitions = [
            {u'available': False, u'name': u'submit', u'target': u'submitted'},
            {u'available': False, u'name': u'close', u'target': u'closed'},
            {u'available': False, u'name': u'approve', u'target': u'approved'}
        ]
        transitions = [
            {u'available': False, u'name': u'reviewed', u'target': u'open'}
        ]
        self.assertEqual(data['data']['meta']['review-transitions'], review_transitions)
        self.assertEqual(data['data']['meta']['transitions'], transitions)

        validations = get_included(response, 'activities/assignment-validations')
        self.assertEqual(validations['attributes']['is-online'][0]['title'],
                         u'This field may not be null.')
        self.assertEqual(validations['attributes']['end-date-type'][0]['title'],
                         u'This field may not be null.')
        self.assertEqual(validations['attributes']['duration'][0]['title'],
                         u'This field may not be null.')
        self.assertEqual(validations['attributes']['location'][0]['title'],
                         u"This field is required or select 'Online'")

    def test_check_validations_complete(self):
        response = self.client.get(
            self.assignment_url,
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        review_transitions = [
            {u'available': True, u'name': u'submit', u'target': u'submitted'},
            {u'available': False, u'name': u'close', u'target': u'closed'},
            {u'available': False, u'name': u'approve', u'target': u'approved'}
        ]
        transitions = [
            {u'available': False, u'name': u'reviewed', u'target': u'open'}
        ]
        self.assertEqual(data['data']['meta']['review-transitions'], review_transitions)
        self.assertEqual(data['data']['meta']['transitions'], transitions)
        validations = get_included(response, 'activities/assignment-validations')
        self.assertEqual(validations['attributes']['is-online'], None)
        self.assertEqual(validations['attributes']['duration'], None)
        self.assertEqual(validations['attributes']['location'], None)

    def test_check_validations_require_location(self):
        self.assignment.is_online = False
        self.assignment.save()
        response = self.client.get(
            self.assignment_url,
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        validations = get_included(response, 'activities/assignment-validations')
        self.assertEqual(validations['attributes']['location'][0]['title'],
                         u"This field is required or select 'Online'")

    def test_submit_owner(self):
        # Owner can submit the assignment
        response = self.client.post(
            self.review_transition_url,
            json.dumps(self.review_data),
            user=self.owner
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)
        self.assertEqual(data['included'][0]['type'], 'activities/assignments')
        self.assertEqual(data['included'][0]['attributes']['review-status'], 'submitted')

    def test_submit_other_user(self):
        # Other user can't submit the assignment
        response = self.client.post(
            self.review_transition_url,
            json.dumps(self.review_data),
            user=self.other_user
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data['errors'][0], "Transition is not available")

    def test_submit_manager(self):
        # Activity manager can submit the assignment
        response = self.client.post(
            self.review_transition_url,
            json.dumps(self.review_data),
            user=self.manager
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['included'][0]['type'], 'activities/assignments')
        self.assertEqual(data['included'][0]['attributes']['review-status'], 'submitted')

    def test_approve_owner(self):
        # Owner should not be allowed to approve own assignment
        self.review_data['data']['attributes']['transition'] = 'approve'
        response = self.client.post(
            self.review_transition_url,
            json.dumps(self.review_data),
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data['errors'][0], "Transition is not available")

    def test_close(self):
        # Owner should not be allowed to close own assignment
        self.transition_data['data']['attributes']['transition'] = 'close'
        response = self.client.post(
            self.transition_url,
            json.dumps(self.transition_data),
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data['errors'][0], "Transition is not available")
