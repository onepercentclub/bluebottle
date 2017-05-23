from django.utils import timezone
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.projects.models import Project

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory


class TestProjectTestCase(BluebottleTestCase):
    def setUp(self):
        super(TestProjectTestCase, self).setUp()
        self.init_projects()

    def test_fake(self):
        self.assertEquals(Project.objects.count(), 0)
        ProjectFactory.create()
        self.assertEquals(Project.objects.count(), 1)


class TestProjectDonationsStatusChanges(BluebottleTestCase):

    def setUp(self):
        super(TestProjectDonationsStatusChanges, self).setUp()
        self.init_projects()

    def test_status_overfunded_projects(self):
        """ Overfunded projects should have status 'done-complete' """
        project = ProjectFactory.create(title='test', amount_asked=100)
        project.status = ProjectPhase.objects.get(slug='campaign')
        project.save()

        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=project,
            order=order,
            amount=110
        )

        donation.save()

        order.locked()
        order.save()
        order.success()
        order.save()

        project = Project.objects.get(title='test')
        project.deadline = timezone.now() - timezone.timedelta(days=1)
        project.save()

        project = Project.objects.get(title='test')
        self.assertEqual(project.status,
                         ProjectPhase.objects.get(slug='done-complete'))


class TestProjectPeopleCount(BluebottleTestCase):
    def setUp(self):
        super(TestProjectPeopleCount, self).setUp()
        self.init_projects()

        self.project = ProjectFactory.create(title='test', amount_asked=100)
        self.project.status = ProjectPhase.objects.get(slug='campaign')
        self.project.save()

        self.user = BlueBottleUserFactory.create()
        self.another_user = BlueBottleUserFactory.create()

        self.task = TaskFactory.create(
            project=self.project, people_needed=10, status='open')
        self.other_task = TaskFactory.create(
            project=self.project, people_needed=10, status='open')

    def test_people_needed(self):
        self.assertEqual(self.project.people_needed, 20)

    def test_people_needed_closed_task(self):
        self.task.status = 'closed'
        self.task.save()

        self.assertEqual(self.project.people_needed, 10)

    def test_people_needed_expired(self):
        self.task.deadline = timezone.now() - timezone.timedelta(days=1)
        self.task.save()

        self.assertEqual(self.project.people_needed, 10)

    def test_people_needed_realized_task(self):
        self.task.status = 'realized'
        self.task.save()

        self.assertEqual(self.project.people_needed, 10)

    def test_people_registered_none(self):
        self.assertEqual(self.project.people_registered, 0)

    def test_people_registered(self):
        TaskMemberFactory.create(member=self.user,
                                 task=self.task)

        self.assertEqual(self.project.people_registered, 1)

    def test_people_registered_externals(self):
        TaskMemberFactory.create(member=self.user,
                                 task=self.task,
                                 externals=3)

        self.assertEqual(self.project.people_registered, 4)

    def test_people_registered_closed_task(self):
        self.task.status = 'closed'
        self.task.save()

        TaskMemberFactory.create(member=self.user,
                                 task=self.task)

        self.assertEqual(self.project.people_registered, 0)

    def test_people_registered_expired_task(self):
        self.task.deadline = timezone.now() - timezone.timedelta(days=1)
        self.task.save()

        TaskMemberFactory.create(member=self.user,
                                 task=self.task)

        self.assertEqual(self.project.people_registered, 1)

    def test_people_registered_not_accepted(self):
        TaskMemberFactory.create(member=self.user,
                                 status='open',
                                 task=self.task)

        self.assertEqual(self.project.people_registered, 0)

    def test_people_registered_for_two_tasks(self):
        TaskMemberFactory.create(member=self.user,
                                 task=self.task)

        TaskMemberFactory.create(member=self.user,
                                 task=self.other_task)

        self.assertEqual(self.project.people_registered, 2)
