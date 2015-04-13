from django.core.management import call_command

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.projects.models import Project
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.tasks import TaskFactory
from bluebottle.tasks.models import Task
from django.utils import timezone


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
        donation.order.succeeded()
        donation.order.save()

        some_project.status = self.campaign
        some_project.save()

        call_command('cron_status_realised', 'test')

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
        donation.order.succeeded()
        donation.order.save()

        some_project.status = self.campaign
        some_project.save()

        call_command('cron_status_realised', 'test')

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
        donation.order.succeeded()
        donation.order.save()

        some_project.status = self.campaign
        some_project.save()

        call_command('cron_status_realised', 'test')

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
        donation.order.succeeded()
        donation.order.save()

        some_project.status = self.campaign
        some_project.save()

        call_command('cron_status_realised', 'test')

        project = Project.objects.get(title='test')
        self.assertEqual(project.status, self.complete)

    def test_task_status_changed(self):
        """
        Test that tasks with (only) status 'in progress' and that are passed
        their deadline get the status 'realized'
        """
        now = timezone.now()

        task = TaskFactory.create(title='task1', status='in progress',
                                  deadline=now - timezone.timedelta(days=5))
        task2 = TaskFactory.create(title='task2', status='open',
                                   deadline=now - timezone.timedelta(days=5))

        self.assertEqual(task.status, 'in progress')
        self.assertEqual(task2.status, 'open')

        call_command('cron_status_realised', 'test')

        task1 = Task.objects.get(title='task1')
        task2 = Task.objects.get(title='task2')

        self.assertEqual(task1.status, 'realized')
        self.assertEqual(task2.status, 'open')
