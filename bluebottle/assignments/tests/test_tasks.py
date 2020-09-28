import mock
from datetime import timedelta
from django.core import mail
from django.db import connection
from django.utils import timezone
from django.utils.timezone import now

from bluebottle.assignments.models import Applicant
from bluebottle.assignments.tasks import assignment_tasks
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

    def test_assignment_reminder_task_deadline(self):
        user = BlueBottleUserFactory.create(first_name='Nono')
        end = now() + timedelta(days=4)
        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            end_date_type='deadline',
            initiative=self.initiative,
            date=end
        )

        ApplicantFactory.create_batch(2, activity=assignment, status='new')
        ApplicantFactory.create(activity=assignment, status='accepted')
        withdrawn = ApplicantFactory.create(activity=assignment, status='new')
        withdrawn.states.withdraw(save=True)

        mail.outbox = []
        tenant = connection.tenant
        assignment_tasks()

        with LocalTenant(tenant, clear_tenant=True):
            assignment.refresh_from_db()

        recipients = [message.to[0] for message in mail.outbox]

        for applicant in assignment.contributions.instance_of(Applicant).all():
            if applicant.status in ['new', 'accepted']:
                self.assertTrue(applicant.user.email in recipients)
            else:
                self.assertFalse(applicant.user.email in recipients)
        self.assertEqual(
            mail.outbox[0].subject,
            'The deadline for your task "{}" is getting close'.format(assignment.title)
        )

    def test_assignment_reminder_task_on_date(self):
        user = BlueBottleUserFactory.create(first_name='Nono')
        end = now() + timedelta(days=4)
        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            end_date_type='on_date',
            initiative=self.initiative,
            date=end
        )

        ApplicantFactory.create_batch(2, activity=assignment, status='new')
        ApplicantFactory.create(activity=assignment, status='accepted')
        withdrawn = ApplicantFactory.create(activity=assignment, status='new')
        withdrawn.states.withdraw(save=True)

        mail.outbox = []
        tenant = connection.tenant
        assignment_tasks()

        with LocalTenant(tenant, clear_tenant=True):
            assignment.refresh_from_db()

        recipients = [message.to[0] for message in mail.outbox]

        for applicant in assignment.contributions.instance_of(Applicant).all():
            if applicant.status in ['new', 'accepted']:
                self.assertTrue(applicant.user.email in recipients)
            else:
                self.assertFalse(applicant.user.email in recipients)
        self.assertEqual(
            mail.outbox[0].subject,
            '"{}" will take place in 5 days!'.format(assignment.title)
        )

    def test_assignment_reminder_task_twice(self):
        user = BlueBottleUserFactory.create(first_name='Nono')
        end = now() + timedelta(days=4)
        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            initiative=self.initiative,
            date=end,
        )

        ApplicantFactory.create_batch(3, activity=assignment, status='new')
        withdrawn = ApplicantFactory.create(activity=assignment, status='new')
        withdrawn.states.withdraw(save=True)

        assignment_tasks()
        mail.outbox = []
        assignment_tasks()

        self.assertEqual(len(mail.outbox), 0)

    def test_assignment_check_registration_deadline(self):
        user = BlueBottleUserFactory.create(first_name='Nono')

        deadline = now() - timedelta(days=1)
        end = now() + timedelta(days=4)

        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            capacity=3,
            end_date_type='on_date',
            registration_deadline=deadline.date(),
            initiative=self.initiative,
            duration=4,
            date=end,
        )
        applicants = ApplicantFactory.create_batch(3, activity=assignment, status='new')
        for applicant in applicants:
            applicant.states.accept(save=True)

        tenant = connection.tenant
        assignment_tasks()

        with LocalTenant(tenant, clear_tenant=True):
            assignment.refresh_from_db()

        self.assertEqual(assignment.status, 'full')

    def test_assignment_check_start_date(self):
        user = BlueBottleUserFactory.create(first_name='Nono')

        registration_deadline = now() - timedelta(days=1)
        date = now() + timedelta(hours=6)

        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            capacity=3,
            registration_deadline=registration_deadline.date(),
            initiative=self.initiative,
            end_date_type='on_date',
            duration=10,
            date=date
        )
        applicants = ApplicantFactory.create_batch(3, activity=assignment, status='new')
        for applicant in applicants:
            applicant.states.accept(save=True)

        tenant = connection.tenant
        with mock.patch.object(timezone, 'now', return_value=(timezone.now() + timedelta(hours=7))):
            assignment_tasks()

        with LocalTenant(tenant, clear_tenant=True):
            assignment.refresh_from_db()

        self.assertEqual(assignment.status, 'running')

    def test_assignment_check_start_date_no_applicants(self):
        user = BlueBottleUserFactory.create(first_name='Nono')

        deadline = now() - timedelta(days=1)
        date = now() - timedelta(hours=2)

        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            capacity=3,
            registration_deadline=deadline.date(),
            initiative=self.initiative,
            duration=10,
            date=date
        )
        tenant = connection.tenant
        assignment_tasks()

        with LocalTenant(tenant, clear_tenant=True):
            assignment.refresh_from_db()

        self.assertEqual(assignment.status, 'cancelled')

    def test_assignment_check_end_date(self):
        user = BlueBottleUserFactory.create(first_name='Nono')

        deadline = now() - timedelta(days=4)
        date = now() - timedelta(days=2)

        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            capacity=3,
            registration_deadline=deadline.date(),
            initiative=self.initiative,
            date=date,
        )

        ApplicantFactory.create_batch(3, activity=assignment)

        tenant = connection.tenant
        assignment_tasks()

        with LocalTenant(tenant, clear_tenant=True):
            assignment.refresh_from_db()

        self.assertEqual(assignment.status, 'succeeded')
        for applicant in assignment.applicants:
            self.assertEqual(applicant.status, 'succeeded')

    def test_assignment_check_end_date_future(self):
        user = BlueBottleUserFactory.create(first_name='Nono')

        deadline = now() - timedelta(days=4)
        date = now() + timedelta(days=2)

        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            capacity=3,
            registration_deadline=deadline.date(),
            initiative=self.initiative,
            date=date,
        )

        applicants = ApplicantFactory.create_batch(3, activity=assignment)
        for applicant in applicants:
            applicant.states.accept(save=True)

        ApplicantFactory.create_batch(3, activity=assignment)

        tenant = connection.tenant

        future = timezone.now() + timedelta(days=3)
        with mock.patch.object(timezone, 'now', return_value=future):
            assignment_tasks()

        with LocalTenant(tenant, clear_tenant=True):
            assignment.refresh_from_db()

        self.assertEqual(assignment.status, 'succeeded')
        for applicant in assignment.applicants:
            self.assertEqual(applicant.status, 'succeeded')
