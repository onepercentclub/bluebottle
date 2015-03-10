from decimal import Decimal

from bluebottle.utils.utils import StatusDefinition

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.test.factory_models.orders import OrderFactory

from bluebottle.statistics.models import Statistic
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.tasks.models import Task


# ('donated', 'projects_online', 'projects_realized', 'tasks_realized', 'people_involved')
class StatisticsTest(BluebottleTestCase):

    def setUp(self):
        super(StatisticsTest, self).setUp()

        self.stats = Statistic.objects.create()

        # Required by Project model save method
        self.init_projects()

        self.some_user = BlueBottleUserFactory.create()
        self.another_user = BlueBottleUserFactory.create()

        self.some_project = ProjectFactory.create(amount_asked=5000, owner=self.some_user)
        self.task = None
        self.donation = None
        self.order = None

    def tearDown(self):
        self.stats.clear_cached()

    def test_initial_stats(self):
        self.assertEqual(self.stats.projects_online, 0)
        self.assertEqual(self.stats.projects_realized, 0)
        self.assertEqual(self.stats.tasks_realized, 0)
        self.assertEqual(self.stats.people_involved, 0)
        self.assertEqual(self.stats.donated, '000')

    def test_project_campaign_stats(self):
        self.some_project.status = ProjectPhase.objects.get(slug='campaign')
        self.some_project.save()

        self.assertEqual(self.stats.projects_online, 1)
        self.assertEqual(self.stats.people_involved, 1)

    def test_project_complete_stats(self):
        self.some_project.status = ProjectPhase.objects.get(slug='done-complete')
        self.some_project.save()

        self.assertEqual(self.stats.projects_online, 0)
        self.assertEqual(self.stats.projects_realized, 1)
        self.assertEqual(self.stats.people_involved, 1)

    def test_task_stats(self):
        self.assertEqual(self.stats.tasks_realized, 0)
        
        # project is in campaign phase
        self.some_project.status = ProjectPhase.objects.get(slug='campaign')
        self.some_project.save()

        # Create a task and add other user as member
        self.task = TaskFactory.create(author=self.some_user, project=self.some_project, status=Task.TaskStatuses.realized)
        TaskMemberFactory.create(task=self.task, member=self.another_user)

        self.assertEqual(self.stats.tasks_realized, 1)
        self.assertEqual(self.stats.people_involved, 2)
        
    def test_donation_stats(self):
        self.order = OrderFactory.create(user=self.another_user, status=StatusDefinition.SUCCESS)
        self.donation = DonationFactory.create(amount=1000, order=self.order)

        self.assertEqual(self.stats.donated, 1000)
        self.assertEqual(self.stats.people_involved, 2)
