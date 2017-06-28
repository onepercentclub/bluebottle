from mock import patch

from django.core.management import call_command
from django.utils import timezone
from django.db import connection
from django.core import mail
from django.test.utils import override_settings

from tenant_schemas.utils import get_tenant_model

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.projects.models import Project
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.tasks.models import Task
from bluebottle.clients.utils import LocalTenant


@override_settings(SEND_WELCOME_MAIL=False)
class TestStatusMC(BluebottleTestCase):
    def setUp(self):
        super(TestStatusMC, self).setUp()

        self.init_projects()
        self.incomplete = ProjectPhase.objects.get(slug="done-incomplete")
        self.complete = ProjectPhase.objects.get(slug="done-complete")
        self.campaign = ProjectPhase.objects.get(slug="campaign")
        self.closed = ProjectPhase.objects.get(slug="closed")

    def test_less_than_20_done_stopped(self):
        """
        Test that a campaign with 20 euros or less and hits the deadline gets
        the status "Done-stopped"
        """
        now = timezone.now()

        some_project = ProjectFactory.create(title='test',
                                             amount_asked=500,
                                             campaign_started=now - timezone.
                                             timedelta(days=15),
                                             deadline=now - timezone.
                                             timedelta(days=5))

        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=some_project,
            order=order,
            amount=20
        )
        donation.save()

        # Set status of donation to paid
        donation.order.locked()
        donation.order.save()
        donation.order.success()
        donation.order.save()

        some_project.status = self.campaign
        some_project.save()

        call_command('cron_status_realised')

        project = Project.objects.get(title='test')
        self.assertEqual(project.status, self.closed)

    def test_no_campaign_started_date(self):
        """
        Test that a campaign that never started gets the phase stopped.
        """
        now = timezone.now()

        some_project = ProjectFactory.create(title='test',
                                             amount_asked=500,
                                             deadline=now - timezone.
                                             timedelta(days=5))

        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=some_project,
            order=order,
            amount=20
        )
        donation.save()

        # Set status of donation to paid
        donation.order.locked()
        donation.order.save()
        donation.order.success()
        donation.order.save()

        some_project.status = self.campaign
        some_project.save()

        call_command('cron_status_realised')

        project = Project.objects.get(title='test')
        self.assertEqual(project.status, self.closed)

    def test_more_than_20_not_fully_funded(self):
        """
        Test that a campaign with more than 20 euros but is not fully funded,
        and hits the deadline gets the status done-incomplete
        """
        now = timezone.now()

        some_project = ProjectFactory.create(title='test',
                                             amount_asked=500,
                                             campaign_started=now - timezone.
                                             timedelta(days=15),
                                             deadline=now - timezone.
                                             timedelta(days=5))

        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=some_project,
            order=order,
            amount=21
        )
        donation.save()

        # Set status of donation to paid
        donation.order.locked()
        donation.order.save()
        donation.order.success()
        donation.order.save()

        some_project.status = self.campaign
        some_project.save()

        call_command('cron_status_realised')

        project = Project.objects.get(title='test')
        self.assertEqual(project.status, self.incomplete)

    def test_fully_funded(self):
        """
        Test that a campaign that is fully funded
        and hits the deadline gets the status done-complete
        """
        now = timezone.now()

        some_project = ProjectFactory.create(title='test',
                                             amount_asked=500,
                                             campaign_started=now - timezone.
                                             timedelta(days=15),
                                             deadline=now - timezone.
                                             timedelta(days=5))

        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=some_project,
            order=order,
            amount=500
        )
        donation.save()

        # Set status of donation to paid
        donation.order.locked()
        donation.order.save()
        donation.order.success()
        donation.order.save()

        some_project.status = self.campaign
        some_project.save()

        call_command('cron_status_realised')

        project = Project.objects.get(title='test')
        self.assertEqual(project.status, self.complete)

    def test_fully_funded_before_deadline(self):
        """
        Test that a campaign that is fully funded
        and hits the deadline gets the status done-complete
        """
        now = timezone.now()

        some_project = ProjectFactory.create(title='test',
                                             amount_asked=500,
                                             campaign_started=now - timezone.
                                             timedelta(days=15),
                                             deadline=now + timezone.
                                             timedelta(days=5))

        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=some_project,
            order=order,
            amount=500
        )
        donation.save()

        # Set status of donation to paid
        donation.order.locked()
        donation.order.save()
        donation.order.success()
        donation.order.save()

        some_project.status = self.campaign
        some_project.save()

        call_command('cron_status_realised')

        project = Project.objects.get(title='test')
        self.assertTrue(project.campaign_funded)

    def test_task_status_changed(self):
        """
        Test that tasks with (only) status 'in progress' and that are passed
        their deadline get the status 'realized'
        """
        now = timezone.now()
        project = ProjectFactory.create(status=ProjectPhase.objects.get(slug='campaign'))

        task1 = TaskFactory.create(title='task1', people_needed=5,
                                   project=project,
                                   deadline=now + timezone.timedelta(days=5))
        task2 = TaskFactory.create(title='task2', people_needed=5,
                                   project=project,
                                   deadline=now + timezone.timedelta(days=5))
        task3 = TaskFactory.create(title='task3', people_needed=5,
                                   project=project, type='event',
                                   deadline=now + timezone.timedelta(days=5))

        TaskMemberFactory.create(task=task1, status='accepted')
        TaskMemberFactory.create_batch(5, task=task3, status='accepted')
        self.assertEquals(len(mail.outbox), 6)

        task1 = Task.objects.get(title='task1')
        task2 = Task.objects.get(title='task2')
        task3 = Task.objects.get(title='task3')

        # Check task statuses
        self.assertEqual(task1.status, 'open')
        self.assertEqual(task2.status, 'open')
        self.assertEqual(task3.status, 'full')

        # Change deadline so we can finish the tasks
        Task.objects.update(deadline=now - timezone.timedelta(days=5))

        call_command('cron_status_realised')

        task1 = Task.objects.get(title='task1')
        task2 = Task.objects.get(title='task2')
        task3 = Task.objects.get(title='task3')

        self.assertEqual(task1.status, 'realized')
        self.assertEqual(task2.status, 'closed')
        self.assertEqual(task3.status, 'realized')

        # Expect two extra mails for task owners
        self.assertEquals(len(mail.outbox), 8)

    def test_task_ignored_non_active_project(self):
        """
        Task that are connected to a project that hasn't started yet should be ignored.
        """
        now = timezone.now()
        project = ProjectFactory.create(status=ProjectPhase.objects.get(slug='plan-new'))

        task = TaskFactory.create(title='task1', people_needed=2,
                                  project=project, status='open',
                                  deadline=now - timezone.timedelta(days=5))

        TaskMemberFactory.create(task=task, status='accepted')
        self.assertEquals(len(mail.outbox), 1)

        call_command('cron_status_realised')

        # There should not be additional mails
        self.assertEquals(len(mail.outbox), 1)

        # Task should still be open
        task1 = Task.objects.get(title='task1')
        self.assertEquals(task1.status, 'open')

    def test_task_status_changes(self):
        """
        Test that tasks changes status.
        """
        now = timezone.now()

        task1 = TaskFactory.create(title='My Task', people_needed=2,
                                   status='open', type='event',
                                   deadline_to_apply=now - timezone.timedelta(days=5),
                                   deadline=now + timezone.timedelta(days=5))

        task2 = TaskFactory.create(title='My Task 2', people_needed=4,
                                   status='open', type='ongoing',
                                   deadline_to_apply=now - timezone.timedelta(days=5),
                                   deadline=now + timezone.timedelta(days=5))

        TaskMemberFactory.create(task=task1, status='accepted')
        TaskMemberFactory.create(task=task1, status='accepted')
        TaskMemberFactory.create_batch(4, task=task2, status='accepted')

        task1 = Task.objects.get(title='My Task')
        self.assertEqual(task1.status, 'full')

        task2 = Task.objects.get(title='My Task 2')
        self.assertEqual(task2.status, 'in progress')

        task1.deadline = now - timezone.timedelta(days=5)
        task1.save()

        task2.deadline = now - timezone.timedelta(days=5)
        task2.save()

        call_command('cron_status_realised')

        task1 = Task.objects.get(title='My Task')
        self.assertEqual(task1.status, 'realized')

        task2 = Task.objects.get(title='My Task 2')
        self.assertEqual(task2.status, 'realized')


@override_settings(SEND_WELCOME_MAIL=False)
class TestMultiTenant(BluebottleTestCase):
    def setUp(self):
        super(TestMultiTenant, self).setUp()

        now = timezone.now()

        self.init_projects()
        self.tenant1 = connection.tenant

        # Create a project for the main tenant
        self.project = ProjectFactory.create(
            status=ProjectPhase.objects.get(slug='campaign'),
            deadline=now - timezone.timedelta(days=5),
            campaign_started=now - timezone.timedelta(days=5),
            amount_asked=0)

        # Create a second tenant
        self.tenant2 = get_tenant_model().objects.get(schema_name='test2')
        connection.set_tenant(self.tenant2)

        self.init_projects()
        self.project2 = ProjectFactory.create(
            status=ProjectPhase.objects.get(slug='campaign'),
            deadline=now - timezone.timedelta(days=5),
            campaign_started=now - timezone.timedelta(days=5),
            amount_asked=0)

    def test_realized_email_multiple_tenants(self):
        with patch.object(LocalTenant, '__new__') as mocked_init:
            call_command('cron_status_realised')

            self.assertEquals(len(mail.outbox), 2)

        self.assertEqual(mocked_init.call_count, 2)
        mocked_init.assert_any_call(LocalTenant, self.tenant1, clear_tenant=True)
        mocked_init.assert_any_call(LocalTenant, self.tenant2, clear_tenant=True)
