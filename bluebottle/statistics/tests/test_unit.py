from moneyed.classes import Money

from bluebottle.utils.utils import StatusDefinition

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.votes import VoteFactory

from bluebottle.statistics.views import Statistics
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.tasks.models import Task


class InitialStatisticsTest(BluebottleTestCase):
    def setUp(self):
        super(InitialStatisticsTest, self).setUp()

        self.stats = Statistics()

        # Required by Project model save method
        self.init_projects()

        self.some_user = BlueBottleUserFactory.create()

        self.some_project = ProjectFactory.create(amount_asked=5000,
                                                  owner=self.some_user)

    def tearDown(self):
        self.stats.clear_cached()

    def test_initial_stats(self):
        self.assertEqual(self.stats.projects_online, 0)
        self.assertEqual(self.stats.projects_realized, 0)
        self.assertEqual(self.stats.tasks_realized, 0)
        self.assertEqual(self.stats.people_involved, 0)
        self.assertEqual(self.stats.donated_total, 0)


class StatisticsTest(BluebottleTestCase):
    def setUp(self):
        super(StatisticsTest, self).setUp()

        self.stats = Statistics()

        # Required by Project model save method
        self.init_projects()

        self.some_user = BlueBottleUserFactory.create()
        self.another_user = BlueBottleUserFactory.create()

        self.campaign_status = ProjectPhase.objects.get(slug='campaign')

        self.some_project = ProjectFactory.create(amount_asked=5000,
                                                  owner=self.some_user)
        self.task = None
        self.donation = None
        self.order = None

    def tearDown(self):
        self.stats.clear_cached()

    def _test_project_stats(self, status, online, involved):
        self.some_project.status = status
        self.some_project.save()

        self.assertEqual(self.stats.projects_online, online)
        # People involved:
        # - campaigner
        self.assertEqual(self.stats.people_involved, involved)

    def test_project_campaign_stats(self):
        self._test_project_stats(
            self.campaign_status,
            online=1,
            involved=1
        )

    def test_project_complete_stats(self):
        self._test_project_stats(
            ProjectPhase.objects.get(
                slug='done-complete'
            ),
            online=0,
            involved=1
        )
        self.assertEqual(self.stats.projects_realized, 1)

    def test_project_voting_stats(self):
        self._test_project_stats(
            ProjectPhase.objects.get(
                slug='voting'
            ),
            online=1,
            involved=1
        )

    def test_project_voting_done_stats(self):
        self._test_project_stats(
            ProjectPhase.objects.get(
                slug='voting-done'
            ),
            online=0,
            involved=1
        )

    def test_project_to_be_continued_stats(self):
        self._test_project_stats(
            ProjectPhase.objects.get(
                slug='to-be-continued'
            ),
            online=0,
            involved=1
        )

    def test_project_draft_stats(self):
        self._test_project_stats(
            ProjectPhase.objects.get(
                slug='plan-new'
            ),
            online=0,
            involved=0
        )

    def test_task_stats(self):
        self.assertEqual(self.stats.tasks_realized, 0)

        # project is in campaign phase
        self.some_project.status = self.campaign_status
        self.some_project.save()

        # Create a task and add other user as member
        self.task = TaskFactory.create(author=self.some_user,
                                       project=self.some_project,
                                       status=Task.TaskStatuses.realized)
        TaskMemberFactory.create(task=self.task, member=self.another_user)

        self.assertEqual(self.stats.tasks_realized, 1)
        # People involved:
        # - campaigner
        # - task member (another_user)
        self.assertEqual(self.stats.people_involved, 2)

    def test_donation_stats(self):
        self.some_project.status = self.campaign_status
        self.some_project.save()

        self.order = OrderFactory.create(user=self.another_user,
                                         status=StatusDefinition.SUCCESS)
        self.donation = DonationFactory.create(amount=Money(1000, 'EUR'), order=self.order,
                                               project=self.some_project,
                                               fundraiser=None)

        self.assertEqual(self.stats.donated_total, 1000)
        # People involved:
        # - campaigner
        # - donator (another_user)
        self.assertEqual(self.stats.people_involved, 2)

    def test_donation_total_stats(self):
        self.some_project.status = self.campaign_status
        self.some_project.save()

        self.order1 = OrderFactory.create(user=self.another_user,
                                          status=StatusDefinition.SUCCESS)
        self.donation1 = DonationFactory.create(amount=Money(1000, 'EUR'), order=self.order1,
                                                project=self.some_project,
                                                fundraiser=None)

        self.order2 = OrderFactory.create(user=None,
                                          status=StatusDefinition.SUCCESS)
        self.donation2 = DonationFactory.create(amount=Money(1000, 'EUR'), order=self.order2,
                                                project=self.some_project,
                                                fundraiser=None)

        self.assertEqual(self.stats.donated_total, 2000)
        # People involved:
        # - campaigner
        # - donator (another_user)
        # - donator (anon)
        self.assertEqual(self.stats.people_involved, 3)

    def test_donation_total_stats_convert_currencies(self):
        self.some_project.status = self.campaign_status
        self.some_project.save()

        self.order1 = OrderFactory.create(user=self.another_user,
                                          status=StatusDefinition.SUCCESS)
        self.donation1 = DonationFactory.create(amount=Money(1000, 'EUR'), order=self.order1,
                                                project=self.some_project,
                                                fundraiser=None)

        self.order2 = OrderFactory.create(user=None,
                                          status=StatusDefinition.SUCCESS)
        self.donation2 = DonationFactory.create(amount=Money(1000, 'USD'), order=self.order2,
                                                project=self.some_project,
                                                fundraiser=None)

        self.assertEqual(self.stats.donated_total, 2500)
        # People involved:
        # - campaigner
        # - donator (another_user)
        # - donator (anon)
        self.assertEqual(self.stats.people_involved, 3)


    def test_votes_stats(self):
        VoteFactory.create(voter=self.some_user)
        VoteFactory.create(voter=self.some_user)
        VoteFactory.create(voter=self.another_user)

        self.assertEqual(self.stats.votes_cast, 3)
