from datetime import timedelta, date

from django.core import mail
from django.db import connection
from django.utils.timezones import now

from bluebottle.assignments.tasks import check_assignment_reminder, check_assignment_registration_deadline, \
    check_assignment_end_date, check_assignment_start_date
from bluebottle.assignments.models import Applicant
from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
from bluebottle.clients.utils import LocalTenant
from bluebottle.initiatives.tests.factories import (
    InitiativePlatformSettingsFactory, InitiativeFactory
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class AssignmentTasksTestCase(BluebottleTestCase):

    def setUp(self):
        super(AssignmentTasksTestCase, self).setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=['assignment']
        )
        self.client = JSONAPITestClient()
        self.initiative = InitiativeFactory.create(status='approved')
        self.initiative.save()

    def test_assignment_reminder_task(self):
        user = BlueBottleUserFactory.create(first_name='Nono')
        end = date.today() + timedelta(days=4)
        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            initiative=self.initiative,
            date=end
        )

        ApplicantFactory.create_batch(2, activity=assignment, status='new')
        ApplicantFactory.create(activity=assignment, status='accepted')
        withdrawn = ApplicantFactory.create(activity=assignment, status='new')
        withdrawn.transitions.withdraw()

        mail.outbox = []
        tenant = connection.tenant
        check_assignment_reminder()

        with LocalTenant(tenant, clear_tenant=True):
            assignment.refresh_from_db()

        recipients = [message.to[0] for message in mail.outbox]

        for applicant in assignment.contributions.instance_of(Applicant).all():
            if applicant.status in ['new', 'accepted']:
                self.assertTrue(applicant.user.email in recipients)
            else:
                self.assertFalse(applicant.user.email in recipients)

        mail.outbox = []

    def test_assignment_reminder_task_twice(self):
        user = BlueBottleUserFactory.create(first_name='Nono')
        end = date.today() + timedelta(days=4)
        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            initiative=self.initiative,
            date=end,
        )

        ApplicantFactory.create_batch(3, activity=assignment, status='new')
        withdrawn = ApplicantFactory.create(activity=assignment, status='new')
        withdrawn.transitions.withdraw()

        check_assignment_reminder()
        mail.outbox = []
        check_assignment_reminder()

        self.assertEqual(len(mail.outbox), 0)

    def test_assignment_check_registration_deadline(self):
        user = BlueBottleUserFactory.create(first_name='Nono')

        deadline = now() - timedelta(days=1)
        end = now() + timedelta(days=4)

        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            capacity=5,
            registration_deadline=deadline,
            initiative=self.initiative,
            date=end,
        )

        applicants = ApplicantFactory.create_batch(3, activity=assignment, status='new')
        for applicant in applicants:
            applicant.transitions.accept()
            applicant.save()

        tenant = connection.tenant
        check_assignment_registration_deadline()

        with LocalTenant(tenant, clear_tenant=True):
            assignment.refresh_from_db()

        self.assertEqual(assignment.status, 'full')

    def test_assignment_check_start_date(self):
        user = BlueBottleUserFactory.create(first_name='Nono')

        deadline = now() - timedelta(days=1)
        date = now() - timedelta(days=2)
        end = now() + timedelta(days=4)

        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            capacity=3,
            registration_deadline=deadline,
            initiative=self.initiative,
            date=date,
            end_date=end.date()
        )

        applicants = ApplicantFactory.create_batch(3, activity=assignment, status='new')
        for applicant in applicants:
            applicant.transitions.accept()
            applicant.save()

        tenant = connection.tenant
        check_assignment_start_date()

        with LocalTenant(tenant, clear_tenant=True):
            assignment.refresh_from_db()

        self.assertEqual(assignment.status, 'running')

    def test_assignment_check_end_date(self):
        user = BlueBottleUserFactory.create(first_name='Nono')

        deadline = now() - timedelta(days=4)
        date = now() - timedelta(days=2)

        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            capacity=3,
            registration_deadline=deadline,
            initiative=self.initiative,
            date=date,
        )

        applicants = ApplicantFactory.create_batch(3, activity=assignment, status='new')
        for applicant in applicants:
            applicant.transitions.accept()
            applicant.save()

        tenant = connection.tenant
        check_assignment_end_date()

        with LocalTenant(tenant, clear_tenant=True):
            assignment.refresh_from_db()

        self.assertEqual(assignment.status, 'succeeded')
