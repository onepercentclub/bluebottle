# -*- coding: utf-8 -*-
import json
from datetime import timedelta

from django.core import mail
from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status

from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
from bluebottle.files.tests.factories import DocumentFactory
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

    def test_create_assignment_missing_data(self):
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

        self.assertTrue(
            '/data/attributes/title' in (
                error['source']['pointer'] for error in response.json()['data']['meta']['required']
            )
        )
        self.assertTrue(
            '/data/attributes/end-date-type' in (
                error['source']['pointer'] for error in response.json()['data']['meta']['required']
            )
        )

        self.assertTrue(
            '/data/attributes/is-online' in (
                error['source']['pointer'] for error in response.json()['data']['meta']['required']
            )
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
        self.assertTrue(
            '/data/attributes/registration-deadline' in (
                error['source']['pointer'] for error in response.json()['data']['meta']['errors']
            )
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
            initiative=self.initiative,
            is_online=None,
            duration=None,
            end_date_type=None,
            end_date=None
        )
        self.assignment = AssignmentFactory.create(
            owner=self.owner,
            initiative=self.initiative
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
            {u'available': False, u'name': u'reviewed', u'target': u'open'},
            {u'available': False, u'name': u'close', u'target': u'closed'}
        ]
        self.assertEqual(data['data']['meta']['review-transitions'], review_transitions)
        self.assertEqual(data['data']['meta']['transitions'], transitions)

        self.assertTrue(
            '/data/attributes/is-online' in (
                error['source']['pointer'] for error in response.json()['data']['meta']['required']
            )
        )
        self.assertTrue(
            '/data/attributes/end-date-type' in (
                error['source']['pointer'] for error in response.json()['data']['meta']['required']
            )
        )

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
            {u'available': False, u'name': u'reviewed', u'target': u'open'},
            {u'available': False, u'name': u'close', u'target': u'closed'}
        ]
        self.assertEqual(data['data']['meta']['review-transitions'], review_transitions)
        self.assertEqual(data['data']['meta']['transitions'], transitions)
        self.assertEqual(data['data']['meta']['required'], [])
        self.assertEqual(data['data']['meta']['errors'], [])

    def test_check_validations_require_location(self):
        self.assignment.is_online = False
        self.assignment.location = None
        self.assignment.save()

        response = self.client.get(
            self.assignment_url,
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            '/data/attributes/location' in (
                error['source']['pointer'] for error in response.json()['data']['meta']['errors']
            )
        )

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


class ApplicantAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(ApplicantAPITestCase, self).setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=['assignment']
        )

        self.client = JSONAPITestClient()
        self.url = reverse('applicant-list')
        self.user = BlueBottleUserFactory()
        self.assignment = AssignmentFactory.create(title="Make coffee")
        self.assignment.review_transitions.submit()
        self.assignment.review_transitions.approve()
        self.apply_data = {
            'data': {
                'type': 'contributions/applicants',
                'attributes': {
                    'motivation': 'Pick me! Pick me!',
                },
                'relationships': {
                    'activity': {
                        'data': {
                            'type': 'activities/assignments',
                            'id': self.assignment.id
                        },
                    },
                }
            }
        }

    def test_apply(self):
        response = self.client.post(self.url, json.dumps(self.apply_data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'new')
        self.assertEqual(response.data['motivation'], 'Pick me! Pick me!')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, u'Someone applied to your task Make coffee! 🙌')
        self.assertTrue("Review the application and decide", mail.outbox[0].body)


class ApplicantTransitionAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(ApplicantTransitionAPITestCase, self).setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=['assignment']
        )

        self.client = JSONAPITestClient()
        self.transition_url = reverse('applicant-transition-list')
        self.user = BlueBottleUserFactory()
        self.someone_else = BlueBottleUserFactory()
        self.manager = BlueBottleUserFactory(first_name="Boss")
        self.owner = BlueBottleUserFactory(first_name="Owner")
        self.initiative = InitiativeFactory.create(activity_manager=self.manager)
        self.assignment = AssignmentFactory.create(owner=self.owner, initiative=self.initiative)
        self.assignment.review_transitions.submit()
        self.assignment.review_transitions.approve()
        self.assignment.save()
        document = DocumentFactory.create()
        self.applicant = ApplicantFactory.create(activity=self.assignment, document=document, user=self.user)
        self.participant_url = reverse('applicant-detail', args=(self.applicant.id,))
        self.transition_data = {
            'data': {
                'type': 'contributions/applicant-transitions',
                'attributes': {
                    'transition': 'accept',
                },
                'relationships': {
                    'resource': {
                        'data': {
                            'type': 'contributions/applicants',
                            'id': self.applicant.pk
                        }
                    }
                }
            }
        }

    def test_applicant_document_by_user(self):
        response = self.client.get(self.participant_url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['document']['id'], str(self.applicant.document.id))
        document = get_included(response, 'documents')
        document_url = document['attributes']['link']

        response = self.client.get(document_url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_applicant_document_by_someone_else(self):
        response = self.client.get(self.participant_url, user=self.someone_else)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['document'], None)
        with self.assertRaises(IndexError):
            get_included(response, 'documents')

    def test_retrieve_document_without_signature(self):
        document_url = reverse('applicant-document', args=(self.applicant.id,))
        response = self.client.get(document_url, user=self.someone_else)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_accept_open_assignment(self):
        # Accept by activity manager
        response = self.client.post(self.transition_url, json.dumps(self.transition_data), user=self.manager)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.applicant.refresh_from_db()
        self.assertEqual(self.applicant.status, 'accepted')

    def test_reject_open_assignment(self):
        # Reject by activity manager
        self.transition_data['data']['attributes']['transition'] = 'reject'
        self.transition_data['data']['attributes']['message'] = "Go away!"
        response = self.client.post(self.transition_url, json.dumps(self.transition_data), user=self.manager)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.applicant.refresh_from_db()
        self.assertEqual(self.applicant.status, 'rejected')
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue("Go away!", mail.outbox[1].body)

    def test_accept_by_owner_assignment(self):
        # Accept by assignment owner
        response = self.client.post(self.transition_url, json.dumps(self.transition_data), user=self.owner)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.applicant.refresh_from_db()
        self.assertEqual(self.applicant.status, 'accepted')
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue("you have been accepted" in mail.outbox[1].body)

    def test_accept_by_owner_assignment_custom_message(self):
        # Accept by assignment owner
        self.transition_data['data']['attributes']['message'] = "See you there!"
        response = self.client.post(self.transition_url, json.dumps(self.transition_data), user=self.owner)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.applicant.refresh_from_db()
        self.assertEqual(self.applicant.status, 'accepted')
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue("See you there!" in mail.outbox[1].body)

    def test_accept_by_self_assignment(self):
        # Applicant should not be able to accept self
        response = self.client.post(self.transition_url, json.dumps(self.transition_data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accept_by_guest_assignment(self):
        # Applicant should not be able to accept self
        response = self.client.post(self.transition_url, json.dumps(self.transition_data))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_by_self_assignment(self):
        # Applicant should not be able to reject self
        self.transition_data['data']['attributes']['transition'] = 'reject'
        response = self.client.post(self.transition_url, json.dumps(self.transition_data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_withdraw_by_self_assignment(self):
        # Withdraw by applicant
        self.transition_data['data']['attributes']['transition'] = 'withdraw'
        response = self.client.post(self.transition_url, json.dumps(self.transition_data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.applicant.refresh_from_db()
        self.assertEqual(self.applicant.status, 'withdrawn')

        # Reapply by applicant
        self.transition_data['data']['attributes']['transition'] = 'reapply'
        response = self.client.post(self.transition_url, json.dumps(self.transition_data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.applicant.refresh_from_db()
        self.assertEqual(self.applicant.status, 'new')

    def test_withdraw_by_owner_assignment(self):
        # Withdraw by owner should not be allowed
        self.transition_data['data']['attributes']['transition'] = 'withdraw'
        response = self.client.post(self.transition_url, json.dumps(self.transition_data), user=self.owner)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
