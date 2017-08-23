import datetime

import pendulum
from django.test.utils import override_settings
from django.utils import timezone
from moneyed.classes import Money

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.projects.models import Project
from bluebottle.statistics.participation import Statistics as ParticipationStatistics
from bluebottle.statistics.views import Statistics
from bluebottle.tasks.models import Task
from bluebottle.tasks.models import TaskMember
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.test.factory_models.votes import VoteFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import StatusDefinition


class InitialStatisticsTest(BluebottleTestCase):
    def setUp(self):
        super(InitialStatisticsTest, self).setUp()

        self.stats = Statistics()

        # Required by Project model save method
        self.init_projects()

        self.some_user = BlueBottleUserFactory.create()

        self.some_project = ProjectFactory.create(amount_asked=5000,
                                                  owner=self.some_user)

    def test_initial_stats(self):
        self.assertEqual(self.stats.projects_online, 0)
        self.assertEqual(self.stats.projects_realized, 0)
        self.assertEqual(self.stats.tasks_realized, 0)
        self.assertEqual(self.stats.people_involved, 0)
        self.assertEqual(self.stats.donated_total, Money(0, 'EUR'))


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
)
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
        self.assertEqual(self.stats.projects_complete, 1)

    def test_project_incomplete_stats(self):
        self._test_project_stats(
            ProjectPhase.objects.get(
                slug='done-incomplete'
            ),
            online=0,
            involved=1
        )
        self.assertEqual(self.stats.projects_realized, 1)
        self.assertEqual(self.stats.projects_complete, 0)

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
        # project is in campaign phase
        self.some_project.status = self.campaign_status
        self.some_project.save()

        # Create a task and add other user as member
        self.task = TaskFactory.create(author=self.some_user,
                                       project=self.some_project,
                                       status=Task.TaskStatuses.realized)
        TaskMemberFactory.create(task=self.task, member=self.another_user, status='realized')

        self.assertEqual(self.stats.tasks_realized, 1)
        self.assertEqual(self.stats.task_members, 1)
        self.assertEqual(self.stats.time_spent, 4)
        # People involved:
        # - campaigner
        # - task member (another_user)
        self.assertEqual(self.stats.people_involved, 2)
        self.assertEqual(self.stats.participants, 2)

    def test_task_stats_user_both_owner_and_member(self):
        # project is in campaign phase
        self.some_project.status = self.campaign_status
        self.some_project.save()

        # Create a task and add other user as member
        self.task = TaskFactory.create(author=self.some_user,
                                       project=self.some_project,
                                       status=Task.TaskStatuses.realized)
        TaskMemberFactory.create(task=self.task, member=self.some_user, status='realized')

        self.assertEqual(self.stats.tasks_realized, 1)
        self.assertEqual(self.stats.task_members, 1)
        self.assertEqual(self.stats.time_spent, 4)
        # People involved:
        # - campaigner as both owner and member
        self.assertEqual(self.stats.people_involved, 1)
        self.assertEqual(self.stats.people_involved, 1)

    def test_donation_stats(self):
        self.some_project.status = self.campaign_status
        self.some_project.save()

        self.order = OrderFactory.create(user=self.another_user,
                                         status=StatusDefinition.SUCCESS)
        self.donation = DonationFactory.create(amount=Money(1000, 'EUR'), order=self.order,
                                               project=self.some_project,
                                               fundraiser=None)

        self.assertEqual(self.stats.donated_total, Money(1000, 'EUR'))
        # People involved:
        # - campaigner
        # - donator (another_user)
        self.assertEqual(self.stats.people_involved, 2)
        self.assertEqual(self.stats.participants, 1)

    def test_donation_pledged_stats(self):
        self.some_project.status = self.campaign_status
        self.some_project.save()

        self.order = OrderFactory.create(user=self.another_user,
                                         status=StatusDefinition.PLEDGED)
        self.donation = DonationFactory.create(amount=Money(1000, 'EUR'), order=self.order,
                                               project=self.some_project,
                                               fundraiser=None)

        self.assertEqual(self.stats.donated_total, Money(1000, 'EUR'))
        self.assertEqual(self.stats.pledged_total, Money(1000, 'EUR'))

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

        self.assertEqual(self.stats.donated_total, Money(2000, 'EUR'))
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

        self.assertEqual(self.stats.donated_total, Money(2500, 'EUR'))
        # People involved:
        # - campaigner
        # - donator (another_user)
        # - donator (anon)
        self.assertEqual(self.stats.people_involved, 3)

    def test_matched_stats(self):
        complete_status = ProjectPhase.objects.get(slug='done-complete')
        ProjectFactory.create(
            amount_asked=Money(1000, 'EUR'),
            amount_extra=Money(100, 'EUR'),
            owner=self.some_user,
            status=complete_status
        )

        ProjectFactory.create(
            amount_asked=Money(1000, 'USD'),
            amount_extra=Money(100, 'USD'),
            owner=self.some_user,
            status=complete_status
        )

        self.assertEqual(self.stats.amount_matched, Money(250, 'EUR'))

    def test_votes_stats(self):
        VoteFactory.create(voter=self.some_user)
        VoteFactory.create(voter=self.some_user)
        VoteFactory.create(voter=self.another_user)

        self.assertEqual(self.stats.votes_cast, 3)


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
)
class StatisticsDateTest(BluebottleTestCase):
    def setUp(self):
        super(StatisticsDateTest, self).setUp()

        self.init_projects()

        new_user = BlueBottleUserFactory.create()
        old_user = BlueBottleUserFactory.create()

        status_realized = ProjectPhase.objects.get(slug='done-complete')
        status_campaign = ProjectPhase.objects.get(slug='campaign')

        now = timezone.now()
        last_year = timezone.now() - datetime.timedelta(days=365)

        new_project = ProjectFactory.create(
            amount_asked=5000, status=status_realized, owner=old_user,
            campaign_ended=now, campaign_started=now
        )
        ProjectFactory.create(
            amount_asked=5000, status=status_campaign, owner=old_user,
            campaign_started=now
        )
        old_project = ProjectFactory.create(
            amount_asked=5000, status=status_realized, owner=old_user,
            campaign_ended=last_year, campaign_started=last_year
        )
        ProjectFactory.create(
            amount_asked=5000, status=status_campaign, owner=old_user,
            campaign_started=last_year
        )

        VoteFactory.create(voter=old_user, created=now)
        vote = VoteFactory.create(voter=old_user)
        vote.created = last_year
        vote.save()

        old_task = TaskFactory.create(
            author=old_user, project=old_project, status=Task.TaskStatuses.realized,
            deadline=last_year
        )
        TaskMemberFactory.create(task=old_task, member=old_user, status='realized')

        new_task = TaskFactory.create(
            author=old_user, project=new_project, status=Task.TaskStatuses.realized,
            deadline=now
        )
        TaskMemberFactory.create(task=new_task, member=new_user, status='realized')

        order1 = OrderFactory.create(user=old_user, status=StatusDefinition.SUCCESS,
                                     confirmed=now)
        DonationFactory.create(
            amount=Money(1000, 'EUR'), order=order1, project=old_project,
            fundraiser=None
        )

        order2 = OrderFactory.create(user=old_user, status=StatusDefinition.SUCCESS,
                                     confirmed=last_year)
        DonationFactory.create(
            amount=Money(1000, 'EUR'), order=order2, project=old_project,
            fundraiser=None
        )

    def test_all(self):
        stats = Statistics()

        self.assertEqual(stats.people_involved, 2)
        self.assertEqual(stats.donated_total, Money(2000, 'EUR'))
        self.assertEqual(stats.projects_online, 2)
        self.assertEqual(stats.projects_realized, 2)
        self.assertEqual(stats.tasks_realized, 2)
        self.assertEqual(stats.votes_cast, 2)

    def test_since_yesterday(self):
        stats = Statistics(start=timezone.now() - datetime.timedelta(days=1))

        self.assertEqual(stats.people_involved, 2)
        self.assertEqual(stats.donated_total, Money(1000, 'EUR'))
        self.assertEqual(stats.projects_online, 1)
        self.assertEqual(stats.projects_realized, 2)
        self.assertEqual(stats.tasks_realized, 2)
        self.assertEqual(stats.votes_cast, 1)

    def test_last_year(self):
        stats = Statistics(
            start=timezone.now() - datetime.timedelta(days=2 * 365),
            end=timezone.now() - datetime.timedelta(days=364),

        )

        self.assertEqual(stats.people_involved, 1)
        self.assertEqual(stats.donated_total, Money(1000, 'EUR'))
        self.assertEqual(stats.projects_online, 1)
        self.assertEqual(stats.projects_realized, 0)
        self.assertEqual(stats.tasks_realized, 0)
        self.assertEqual(stats.votes_cast, 1)

    def test_since_last_year(self):
        stats = Statistics(
            start=timezone.now() - datetime.timedelta(days=366),
        )

        self.assertEqual(stats.people_involved, 2)
        self.assertEqual(stats.donated_total, Money(2000, 'EUR'))
        self.assertEqual(stats.projects_online, 2)
        self.assertEqual(stats.projects_realized, 2)
        self.assertEqual(stats.tasks_realized, 2)
        self.assertEqual(stats.votes_cast, 2)


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
)
class ParticipationStatisticsTest(BluebottleTestCase):
    def setUp(self):
        super(ParticipationStatisticsTest, self).setUp()

        # Required by Project model save method
        self.init_projects()

        self.user_1 = BlueBottleUserFactory.create()
        self.user_2 = BlueBottleUserFactory.create()
        self.user_3 = BlueBottleUserFactory.create()

        self.project_status_plan_new = ProjectPhase.objects.get(slug='plan-new')
        self.project_status_plan_submitted = ProjectPhase.objects.get(slug='plan-submitted')
        self.project_status_voting = ProjectPhase.objects.get(slug='voting')
        self.project_status_voting_done = ProjectPhase.objects.get(slug='voting-done')
        self.project_status_campaign = ProjectPhase.objects.get(slug='campaign')
        self.project_status_done_complete = ProjectPhase.objects.get(slug='done-complete')
        self.project_status_done_incomplete = ProjectPhase.objects.get(slug='done-incomplete')
        self.project_status_closed = ProjectPhase.objects.get(slug='closed')

        self.some_project = ProjectFactory.create(owner=self.user_1, status=self.project_status_done_complete)
        self.another_project = ProjectFactory.create(owner=self.user_2)

        # NOTE: auto_add_now datefields cannot be overridden in factory object creation methods
        Project.objects.filter(id=self.some_project.id).update(created=pendulum.create(2016, 1, 20))
        Project.objects.filter(id=self.another_project.id).update(created=pendulum.create(2016, 7, 20))

        self.some_task = TaskFactory.create(project=self.some_project,
                                            author=self.user_1,
                                            created=pendulum.create(2016, 1, 30))
        self.another_task = TaskFactory.create(project=self.another_project,
                                               author=self.user_2,
                                               created=pendulum.create(2016, 7, 30))

        Task.objects.filter(id=self.some_task.id).update(created=pendulum.create(2016, 1, 30))
        Task.objects.filter(id=self.another_task.id).update(created=pendulum.create(2016, 7, 30))

        self.some_task_member = TaskMemberFactory.create(member=self.user_1, task=self.some_task)
        self.another_task_member = TaskMemberFactory.create(member=self.user_2, task=self.another_task)

        TaskMember.objects.filter(id=self.some_task_member.id).update(created=pendulum.create(2016, 1, 31))
        TaskMember.objects.filter(id=self.another_task_member.id).update(created=pendulum.create(2016, 7, 31))

        self.statistics = ParticipationStatistics(start=pendulum.create(2016, 1, 1, 0, 0, 0),
                                                  end=pendulum.create(2016, 12, 31, 23, 59, 59))

    def test_participant_details(self):
        # participant_details = self.statistics.participant_details()
        participant_count = self.statistics.participants_count

        self.assertEqual(participant_count, 1)
