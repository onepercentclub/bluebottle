from datetime import timedelta, date

from django.core import mail

from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
from bluebottle.test.utils import BluebottleTestCase


class AssignmentTestCase(BluebottleTestCase):
    def test_absolute_url(self):
        activity = AssignmentFactory()
        expected = 'http://testserver/en/initiatives/activities/' \
                   'details/assignment/{}/{}'.format(activity.id, activity.slug)
        self.assertEqual(activity.get_absolute_url(), expected)

    def test_slug(self):
        assignment = AssignmentFactory(title='Test Title')
        self.assertEqual(
            assignment.slug, 'test-title'
        )

    def test_slug_empty(self):
        assignment = AssignmentFactory(title='')
        self.assertEqual(
            assignment.slug, 'new'
        )

    def test_slug_special_characters(self):
        assignment = AssignmentFactory(title='!!! $$$$')
        self.assertEqual(
            assignment.slug, 'new'
        )

    def test_date_changed(self):
        assignment = AssignmentFactory(
            title='Test Title',
            status='open',
            end_date=date.today() + timedelta(days=4),
        )
        ApplicantFactory.create_batch(3, activity=assignment, status='new')
        withdrawn = ApplicantFactory.create(activity=assignment, status='new')
        withdrawn.transitions.withdraw()

        mail.outbox = []

        assignment.end_date = assignment.end_date + timedelta(days=1)
        assignment.save()

        recipients = [message.to[0] for message in mail.outbox]

        for participant in assignment.contributions.all():
            if participant.status == 'new':
                self.assertTrue(participant.user.email in recipients)
            else:
                self.assertFalse(participant.user.email in recipients)

    def test_date_not_changed(self):
        assignment = AssignmentFactory(
            title='Test Title',
            status='open',
            end_date=date.today() + timedelta(days=4),
        )
        ApplicantFactory.create_batch(3, activity=assignment, status='new')
        withdrawn = ApplicantFactory.create(activity=assignment, status='new')
        withdrawn.transitions.withdraw()

        mail.outbox = []

        assignment.title = 'New title'
        assignment.save()

        self.assertEqual(len(mail.outbox), 0)

    def test_check_status_capacity_changed(self):
        assignment = AssignmentFactory(
            title='Test Title',
            status='open',
            end_date=date.today() + timedelta(days=4),
            capacity=3,
        )
        ApplicantFactory.create_batch(3, activity=assignment, status='accepted')

        self.assertEqual(assignment.status, 'full')

        assignment.capacity = 10
        assignment.save()

        self.assertEqual(assignment.status, 'open')

    def test_check_status_applicant_removed(self):
        assignment = AssignmentFactory(
            title='Test Title',
            status='open',
            end_date=date.today() + timedelta(days=4),
            capacity=3,
        )
        applicants = ApplicantFactory.create_batch(3, activity=assignment, status='accepted')

        self.assertEqual(assignment.status, 'full')

        applicants[0].delete()

        self.assertEqual(assignment.status, 'open')


class ApplicantTestCase(BluebottleTestCase):

    def test_applicant_status_change_on_time_spent(self):
        assignment = AssignmentFactory(
            title='Test Title',
            status='open',
            end_date=date.today() + timedelta(days=4),
        )

        applicant = ApplicantFactory.create(activity=assignment)
        applicant.transitions.accept()
        applicant.save()
        assignment.transitions.succeed()
        assignment.save()
        applicant.refresh_from_db()

        self.assertEqual(applicant.status, 'succeeded')
        applicant.time_spent = 0
        applicant.save()
        self.assertEqual(applicant.status, 'failed')
        applicant.time_spent = 10
        applicant.save()
        self.assertEqual(applicant.status, 'succeeded')
