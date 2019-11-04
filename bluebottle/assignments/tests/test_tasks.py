from datetime import timedelta

from django.core import mail
from django.utils.timezone import now

from bluebottle.assignments.tasks import check_assignment_reminder
from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
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
        end = now() + timedelta(days=4)
        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            initiative=self.initiative,
            end_date=end
        )

        ApplicantFactory.create_batch(3, activity=assignment, status='new')
        withdrawn = ApplicantFactory.create(activity=assignment, status='new')
        withdrawn.transitions.withdraw()

        mail.outbox = []
        check_assignment_reminder()

        recipients = [message.to[0] for message in mail.outbox]

        for applicant in assignment.contributions.all():
            if applicant.status == 'new':
                self.assertTrue(applicant.user.email in recipients)
            else:
                self.assertFalse(applicant.user.email in recipients)

        recipients = [message.to[0] for message in mail.outbox]

        for applicant in assignment.contributions.all():
            if applicant.status == 'new':
                self.assertTrue(applicant.user.email in recipients)
            else:
                self.assertFalse(applicant.user.email in recipients)

        mail.outbox = []

    def test_assignment_reminder_task_twice(self):
        user = BlueBottleUserFactory.create(first_name='Nono')
        end = now() + timedelta(days=4)
        assignment = AssignmentFactory.create(
            owner=user,
            status='open',
            initiative=self.initiative,
            end_date=end,
        )

        ApplicantFactory.create_batch(3, activity=assignment, status='new')
        withdrawn = ApplicantFactory.create(activity=assignment, status='new')
        withdrawn.transitions.withdraw()

        check_assignment_reminder()
        mail.outbox = []
        check_assignment_reminder()

        self.assertEqual(len(mail.outbox), 0)
