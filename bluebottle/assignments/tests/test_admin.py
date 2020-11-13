# -*- coding: utf-8 -*-

from builtins import str
from django.contrib.admin.sites import AdminSite
from django.urls.base import reverse
from rest_framework import status

from bluebottle.assignments.admin import AssignmentAdmin
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class TestAssignmentAdmin(BluebottleAdminTestCase):
    def setUp(self):
        super(TestAssignmentAdmin, self).setUp()
        self.site = AdminSite()
        self.assignment_admin = AssignmentAdmin(Assignment, self.site)
        self.assignment = AssignmentFactory.create(status='created', end_date_type='on_date', preparation=5,)
        self.assignment_url = reverse('admin:assignments_assignment_change', args=(self.assignment.id,))
        self.assignment.save()

    def test_assignment_admin(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.assignment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_assignment_admin(self):
        self.client.force_login(self.superuser)
        ApplicantFactory.create_batch(3, activity=self.assignment)
        url = reverse('admin:assignments_assignment_delete', args=(self.assignment.id,))
        response = self.client.post(url, {'post': 'yes'})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Assignment.objects.count(), 0)
        self.assertEqual(Applicant.objects.count(), 0)

    def test_delete_applicant_assignment_admin(self):
        self.client.force_login(self.superuser)
        self.applicants = ApplicantFactory.create_batch(3, activity=self.assignment, time_spent=6,)
        self.assertEqual(Applicant.objects.count(), 3)
        url = reverse('admin:assignments_assignment_change', args=(self.assignment.id,))

        data = {
            'title': 'New title',
            'slug': self.assignment.slug,
            'image': '',
            'video_url': '',
            'initiative': self.assignment.initiative_id,
            'owner': self.assignment.owner_id,
            'description': self.assignment.description,
            'capacity': self.assignment.capacity,
            'date_0': str(self.assignment.date.date()),
            'date_1': str(self.assignment.date.time()),
            'end_date_type': self.assignment.end_date_type,
            'registration_deadline': str(self.assignment.registration_deadline),
            'duration': self.assignment.duration,
            'preparation': self.assignment.preparation,
            'expertise': self.assignment.expertise_id,
            'is_online': self.assignment.is_online,
            'location': self.assignment.location_id,
            'status': self.assignment.status,
            'force_status': 'open',

            '_continue': 'Save and continue editing',
            'confirm': True,

            'notifications-message-content_type-object_id-TOTAL_FORMS': '0',
            'notifications-message-content_type-object_id-INITIAL_FORMS': '0',
            'wallposts-wallpost-content_type-object_id-TOTAL_FORMS': '0',
            'wallposts-wallpost-content_type-object_id-INITIAL_FORMS': '0',
            'goals-TOTAL_FORMS': '0',
            'goals-INITIAL_FORMS': '0',
            'intentions-TOTAL_FORMS': '3',
            'intentions-INITIAL_FORMS': '3',
            'intentions-0-intention_ptr': self.applicants[0].intention_ptr_id,
            'intentions-0-activity': self.assignment.id,
            'intentions-0-user': self.applicants[0].user_id,
            'intentions-0-time_spent': self.applicants[0].time_spent,
            'intentions-0-motivation': self.applicants[0].motivation,
            'intentions-0-status': self.applicants[0].status,
            'intentions-0-DELETE': 'on',
            'intentions-1-intention_ptr': self.applicants[1].intention_ptr_id,
            'intentions-1-activity': self.assignment.id,
            'intentions-1-user': self.applicants[1].user_id,
            'intentions-1-time_spent': self.applicants[1].time_spent,
            'intentions-1-status': self.applicants[1].status,
            'intentions-2-intention_ptr': self.applicants[2].intention_ptr_id,
            'intentions-2-activity': self.assignment.id,
            'intentions-2-user': self.applicants[2].user_id,
            'intentions-2-time_spent': self.applicants[2].time_spent,
            'intentions-2-status': self.applicants[2].status,
            'intentions-2-DELETE': 'on',
        }

        response = self.client.post(url, data)
        self.assertEqual(
            response.status_code, status.HTTP_302_FOUND,
            'Deleting applicants failed. '
            'Did you change admin fields for AssignmentAdmin? '
            'Please adjust the data in this test.')
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.title, 'New title')
        self.assertEqual(Applicant.objects.count(), 1)

    def test_empty_title_assignment_admin(self):
        self.client.force_login(self.superuser)
        self.applicants = ApplicantFactory.create_batch(3, activity=self.assignment, time_spent=6,)
        self.assertEqual(Applicant.objects.count(), 3)
        url = reverse('admin:assignments_assignment_change', args=(self.assignment.id,))

        data = {
            'title': '',
            'slug': self.assignment.slug,
            'owner': self.assignment.owner_id,
            'initiative': self.assignment.initiative_id,
            'description': self.assignment.description,
            'capacity': self.assignment.capacity,
            'date_0': str(self.assignment.date.date()),
            'date_1': str(self.assignment.date.time()),
            'end_date_type': self.assignment.end_date_type,
            'registration_deadline': str(self.assignment.registration_deadline),
            'duration': self.assignment.duration,
            'preparation': self.assignment.preparation,
            'expertise': self.assignment.expertise_id,
            'is_online': self.assignment.is_online,
            'location': self.assignment.location_id,

            '_continue': 'Save and continue editing',
            'confirm': 'Yes',

            'notifications-message-content_type-object_id-TOTAL_FORMS': '0',
            'notifications-message-content_type-object_id-INITIAL_FORMS': '0',
            'wallposts-wallpost-content_type-object_id-TOTAL_FORMS': '0',
            'wallposts-wallpost-content_type-object_id-INITIAL_FORMS': '0',

            'intentions-TOTAL_FORMS': '3',
            'intentions-INITIAL_FORMS': '3',
            'intentions-0-intention_ptr': self.applicants[0].intention_ptr_id,
            'intentions-0-activity': self.assignment.id,
            'intentions-0-user': self.applicants[0].user_id,
            'intentions-0-time_spent': self.applicants[0].time_spent,
            'intentions-0-DELETE': 'on',
            'intentions-1-intention_ptr': self.applicants[1].intention_ptr_id,
            'intentions-1-activity': self.assignment.id,
            'intentions-1-user': self.applicants[1].user_id,
            'intentions-1-time_spent': self.applicants[1].time_spent,
            'intentions-2-intention_ptr': self.applicants[2].intention_ptr_id,
            'intentions-2-activity': self.assignment.id,
            'intentions-2-user': self.applicants[2].user_id,
            'intentions-2-time_spent': self.applicants[2].time_spent,
            'intentions-2-DELETE': 'on',
        }

        response = self.client.post(url, data)
        self.assertContains(response, '<ul class="errorlist"><li>This field is required.</li></ul>')
