import datetime

import pendulum
from django.test.utils import override_settings
from django.utils import timezone
from moneyed.classes import Money

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.statistics.participation import Statistics as ParticipationStatistics
from bluebottle.statistics.views import Statistics
from bluebottle.tasks.models import Task
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.geo import LocationFactory
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

    def test_donation_stats_named_donation(self):
        self.some_project.status = self.campaign_status
        self.some_project.save()

        order = OrderFactory.create(
            user=self.another_user,
            status=StatusDefinition.SUCCESS)
        self.donation = DonationFactory.create(amount=Money(1000, 'EUR'), order=order,
                                               project=self.some_project,
                                               fundraiser=None)
        order = OrderFactory.create(
            user=self.another_user,
            status=StatusDefinition.SUCCESS)
        self.donation = DonationFactory.create(amount=Money(1000, 'EUR'), order=order,
                                               project=self.some_project,
                                               name='test-name',
                                               fundraiser=None)

        self.assertEqual(self.stats.donated_total, Money(2000, 'EUR'))
        # People involved:
        # - campaigner
        # - donator (another_user)
        # - donator (another_user on behalve of somebody else)
        self.assertEqual(self.stats.people_involved, 3)
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

    def test_members_stats(self):
        BlueBottleUserFactory.create(is_active=False)

        self.assertEqual(self.stats.members, 3)


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
            campaign_ended=now, campaign_started=now, amount_extra=100
        )
        ProjectFactory.create(
            amount_asked=5000, status=status_campaign, owner=old_user,
            campaign_started=now
        )
        old_project = ProjectFactory.create(
            amount_asked=5000, status=status_realized, owner=old_user,
            campaign_ended=last_year, campaign_started=last_year,
            amount_extra=200
        )
        ProjectFactory.create(
            amount_asked=5000, status=status_campaign, owner=old_user,
            campaign_started=last_year, amount_extra=1000
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

        order1 = OrderFactory.create(user=old_user, status=StatusDefinition.SUCCESS)
        order1.created = now
        order1.save()

        DonationFactory.create(
            amount=Money(1000, 'EUR'), order=order1, project=old_project,
            fundraiser=None
        )

        order2 = OrderFactory.create(user=old_user, status=StatusDefinition.SUCCESS)
        order2.created = last_year
        order2.save()

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
        self.assertEqual(stats.amount_matched, Money(1300, 'EUR'))

    def test_since_yesterday(self):
        stats = Statistics(start=timezone.now() - datetime.timedelta(days=1))

        self.assertEqual(stats.people_involved, 2)
        self.assertEqual(stats.donated_total, Money(1000, 'EUR'))
        self.assertEqual(stats.projects_online, 1)
        self.assertEqual(stats.projects_realized, 2)
        self.assertEqual(stats.tasks_realized, 2)
        self.assertEqual(stats.votes_cast, 1)
        self.assertEqual(stats.amount_matched, Money(100, 'EUR'))

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
        self.assertEqual(stats.amount_matched, Money(200, 'EUR'))

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
        self.assertEqual(stats.amount_matched, Money(300, 'EUR'))


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

        self.location = LocationFactory.create()

        self.project_status_plan_new = ProjectPhase.objects.get(slug='plan-new')
        self.project_status_plan_submitted = ProjectPhase.objects.get(slug='plan-submitted')
        self.project_status_voting = ProjectPhase.objects.get(slug='voting')
        self.project_status_voting_done = ProjectPhase.objects.get(slug='voting-done')
        self.project_status_campaign = ProjectPhase.objects.get(slug='campaign')
        self.project_status_done_complete = ProjectPhase.objects.get(slug='done-complete')
        self.project_status_done_incomplete = ProjectPhase.objects.get(slug='done-incomplete')
        self.project_status_closed = ProjectPhase.objects.get(slug='closed')

        self.some_project = ProjectFactory.create(owner=self.user_1,
                                                  status=self.project_status_done_complete,
                                                  location=self.location)
        self.another_project = ProjectFactory.create(owner=self.user_2)

        self.some_task = TaskFactory.create(project=self.some_project,
                                            author=self.user_1)
        self.another_task = TaskFactory.create(project=self.another_project,
                                               author=self.user_2)

        self.some_task_member = TaskMemberFactory.create(member=self.user_1, task=self.some_task)
        self.another_task_member = TaskMemberFactory.create(member=self.user_2, task=self.another_task)

        start = pendulum.create().subtract(days=7)
        end = pendulum.create().add(days=7)

        # TODO: Create atleast one project, task and task member outside the time range

        self.statistics = ParticipationStatistics(start=start,
                                                  end=end)

    def test_participant_details(self):
        participant_count = self.statistics.participants_count

        # NOTE: Participants : One project creator with project status done complete and one task creator
        self.assertEqual(participant_count, 2)

    def test_projects_total(self):
        count = self.statistics.projects_total
        self.assertEqual(count, 2)

    def test_projects_count_by_theme(self):
        count = self.statistics.get_projects_count_by_theme(theme='education')
        self.assertEqual(count, 2)

    def test_projects_count_by_last_status(self):
        count = self.statistics.get_projects_count_by_last_status(statuses=['done-complete'])
        self.assertEqual(count, 1)

    def test_projects_status_count_by_location_group(self):
        count = self.statistics.get_projects_status_count_by_location_group(location_group=self.location.group.name,
                                                                            statuses=['done-complete'])
        self.assertEqual(count, 1)

    def test_projects_status_count_by_theme(self):
        count = self.statistics.get_projects_status_count_by_theme(theme='education', statuses=['done-complete'])
        self.assertEqual(count, 1)

    def test_projects_by_location_group(self):
        count = len(self.statistics.get_projects_by_location_group(location_group=self.location.group.name))
        self.assertEqual(count, 1)

    def test_project_successful(self):
        count = self.statistics.projects_successful
        self.assertEqual(count, 1)

    def test_project_running(self):
        count = self.statistics.projects_running
        self.assertEqual(count, 0)

    def test_project_complete(self):
        count = self.statistics.projects_complete
        self.assertEqual(count, 1)

    def test_project_online(self):
        count = self.statistics.projects_online
        self.assertEqual(count, 0)

    def test_tasks_total(self):
        count = self.statistics.tasks_total
        self.assertEqual(count, 2)

    def test_tasks_count_by_last_status(self):
        count = self.statistics.get_tasks_count_by_last_status(statuses=['in progress'])
        self.assertEqual(count, 2)

    def test_tasks_status_count_by_location_group(self):
        count = self.statistics.get_tasks_status_count_by_location_group(location_group=self.location.group.name,
                                                                         statuses=['in progress'])
        self.assertEqual(count, 1)

    def test_tasks_status_count_by_theme(self):
        count = self.statistics.get_tasks_status_count_by_theme(theme='education', statuses=['in progress'])
        self.assertEqual(count, 2)

    def test_task_members_total(self):
        count = self.statistics.task_members_total
        self.assertEqual(count, 2)

    def test_get_task_members_count_by_last_status(self):
        count = self.statistics.get_task_members_count_by_last_status(['accepted'])
        self.assertEqual(count, 2)

    def test_task_members(self):
        count = self.statistics.task_members
        self.assertEqual(count, 0)

    def test_unconfirmed_task_members(self):
        count = self.statistics.unconfirmed_task_members
        self.assertEqual(count, 0)

    def test_unconfirmed_task_members_task_count(self):
        count = self.statistics.unconfirmed_task_members_task_count
        self.assertEqual(count, 0)
