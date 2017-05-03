from datetime import datetime, timedelta
from moneyed import Money
from django.utils import timezone
from bluebottle.test.utils import BluebottleTestCase
from dashboard import Metrics
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.test.factory_models.suggestions import SuggestionFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.bb_projects.models import ProjectPhase


class MetricsTest(BluebottleTestCase):
    def setUp(self):
        self.init_projects()  # Intialize various objects such as ProjectPhases
        self.metrics = Metrics()
        self.future = datetime.today() + timedelta(days=1)

        self.new = ProjectPhase.objects.get(slug="plan-new")
        self.campaign = ProjectPhase.objects.get(slug="campaign")
        self.done_complete = ProjectPhase.objects.get(slug="done-complete")
        self.done_incomplete = ProjectPhase.objects.get(slug="done-incomplete")
        self.closed = ProjectPhase.objects.get(slug="closed")

    def test_partners_year(self):
        """ Test correct calculation of partners """

        task = TaskFactory(deadline=timezone.now())

        TaskMemberFactory(task=task, externals=1, status='applied')  # count 0
        TaskMemberFactory(task=task, externals=4, status='realized')  # count 4
        TaskMemberFactory(task=task, externals=2, status='accepted')  # count 2
        TaskMemberFactory(task=task, externals=3, status='rejected')  # 0
        TaskMemberFactory(task=task, externals=3, status='stopped')  # 0

        # Only count the task members with externals with allowed statuses (applied, accepted, realized)
        partners, _ = self.metrics.calculate_partner_metrics()
        self.assertEqual(partners[self.metrics.this_year], 6)

    def test_partners_hours(self):
        """ Test correct calculation of hours of partners """

        task = TaskFactory(deadline=timezone.now())

        TaskMemberFactory(task=task, externals=2, status='applied', time_spent=4)  # count 0
        TaskMemberFactory(task=task, externals=4, status='realized', time_spent=4)  # count 4 x 4 = 16
        TaskMemberFactory(task=task, externals=2, status='accepted', time_spent=8)  # count 8 x 2 = 16
        TaskMemberFactory(task=task, externals=3, status='rejected', time_spent=8)  # 0
        TaskMemberFactory(task=task, externals=3, status='stopped', time_spent=4)  # 0

        # Only count the time spent hours of task members with externals
        # with allowed statuses (applied, accepted, realized)
        _, partner_hours = self.metrics.calculate_partner_metrics()
        self.assertEqual(partner_hours[self.metrics.this_year], 32)

    def test_suggestions_empty(self):
        """ No suggestions means all zeroes """
        suggestion_metrics = self.metrics.calculate_suggestion_metrics()

        for key in ("expired", "unconfirmed",
                    "draft", "accepted", "rejected"):
            self.assertEqual(suggestion_metrics[key], 0)

    def test_suggestions_expired(self):
        """ verify suggestions past the deadline are expired """
        yesterday = datetime.today() - timedelta(days=1)

        SuggestionFactory.create(title="expired suggestion", deadline=yesterday, status="submitted")
        suggestion_metrics = self.metrics.calculate_suggestion_metrics()
        self.assertEqual(suggestion_metrics['expired'], 1)

    def test_suggestions_today_not_expired(self):
        """ if the deadline is today, there's still time """
        today = datetime.today()

        SuggestionFactory.create(title="expired suggestion", deadline=today, status="submitted")

        suggestion_metrics = self.metrics.calculate_suggestion_metrics()
        self.assertEqual(suggestion_metrics['expired'], 0)

    def test_suggestions_states(self):
        """ verify all other states / cases are counted properly """

        states = ("unconfirmed", "draft", "accepted", "rejected")

        for state in states:
            SuggestionFactory.create(title="Suggestion with state " + state,
                                     deadline=self.future,
                                     status=state)

        suggestion_metrics = self.metrics.calculate_suggestion_metrics()

        for state in states:
            self.assertEqual(suggestion_metrics[state], 1)

    def test_supporters(self):
        """ Test return value of supporters, users who did a succesful donation """

        ProjectFactory.create(amount_asked=1000)
        user1 = BlueBottleUserFactory.create()
        user2 = BlueBottleUserFactory.create()
        user3 = BlueBottleUserFactory.create()

        order1 = OrderFactory.create(user=user1)
        DonationFactory(order=order1, amount=20)
        order1.locked()
        order1.save()
        order1.failed()
        order1.save()

        order2 = OrderFactory.create(user=user2)
        DonationFactory(order=order2, amount=25)
        order2.locked()
        order2.save()
        order2.success()
        order2.save()

        order3 = OrderFactory.create(user=user2)
        DonationFactory(order=order3, amount=30)
        order3.locked()
        order3.save()
        order3.success()
        order3.save()

        order4 = OrderFactory.create(user=user3)
        DonationFactory(order=order4, amount=35)
        order4.locked()
        order4.save()
        order4.success()
        order4.save()

        # User two should be counted once, and user 3 should be counted
        self.assertEqual(self.metrics.calculate_supporters(), 2)

    def test_total_raised(self):
        """ Calculate the total amount raised by successful donations """
        project1 = ProjectFactory.create(amount_asked=1000)
        project2 = ProjectFactory.create(amount_asked=1000)

        user1 = BlueBottleUserFactory.create()
        user2 = BlueBottleUserFactory.create()
        user3 = BlueBottleUserFactory.create()

        order1 = OrderFactory.create(user=user1)
        DonationFactory(order=order1, amount=10, project=project1)
        order1.locked()
        order1.save()
        order1.failed()
        order1.save()

        order2 = OrderFactory.create(user=user2)
        DonationFactory(order=order2, amount=10, project=project1)
        order2.locked()
        order1.save()
        order2.success()
        order2.save()

        order3 = OrderFactory.create(user=user2)
        DonationFactory(order=order3, amount=10, project=project2)
        order3.locked()
        order3.save()
        order3.success()
        order3.save()

        order4 = OrderFactory.create(user=user3)
        DonationFactory(order=order4, amount=10, project=project1)
        order4.locked()
        order4.save()
        order4.success()
        order4.save()

        # order2, order3, order4 should be counted
        self.assertEqual(self.metrics.calculate_total_raised(), Money(30, 'EUR'))

    def test_initiators(self):
        """
        Test counting project initiators of project with status,
        campaign, done-complete, done-incomplete
        """
        user1 = BlueBottleUserFactory.create()
        user2 = BlueBottleUserFactory.create()
        user3 = BlueBottleUserFactory.create()
        user4 = BlueBottleUserFactory.create()
        user5 = BlueBottleUserFactory.create()

        ProjectFactory.create(status=self.new, owner=user1)
        ProjectFactory.create(status=self.campaign, owner=user2)
        ProjectFactory.create(status=self.done_complete, owner=user3)
        ProjectFactory.create(status=self.done_incomplete, owner=user4)
        ProjectFactory.create(status=self.closed, owner=user5)
        ProjectFactory.create(status=self.campaign, owner=user2)

        # Count user2 (once), user3, and user4
        self.assertEquals(self.metrics.calculate_initiators(), 3)

    def test_taskmember_hours(self):
        """ Test taskmember hours spent calculation, status must be realized """
        task = TaskFactory(time_needed=8)

        TaskMemberFactory(task=task, status='applied')
        TaskMemberFactory(task=task, status='realized')
        TaskMemberFactory(task=task, status='accepted')
        TaskMemberFactory(task=task, status='rejected')
        TaskMemberFactory(task=task, status='stopped')

        TaskMemberFactory(task=task, status='realized')
        TaskMemberFactory(task=task, status='realized')

        # Count tm2, tm6, tm7, 3x8 hours
        _, hours = self.metrics.calculate_taskmember_metrics()
        self.assertEquals(hours, 24)

    def test_realized_tasks_unconfirmed_taskmembers(self):
        """ Test count of realized tasks with unconfirmed taskmembers """

        task1 = TaskFactory(status='realized')
        task2 = TaskFactory(status='open')
        task3 = TaskFactory(status='in_progress')
        task4 = TaskFactory(status='realized')

        # Realized task without realized task member, count
        TaskMemberFactory(task=task1, status='applied')
        TaskMemberFactory(task=task1, status='accepted')
        task1.status = 'realized'
        task1.save()

        # Realized task with realized task member and others, dont count
        TaskMemberFactory(task=task4, status='applied')
        TaskMemberFactory(task=task4, status='accepted')
        TaskMemberFactory(task=task4, status='realized')

        task4.skatus = 'realized'
        task4.save()

        # Open task - Don't count
        TaskMemberFactory(task=task2, status='applied')
        task2.status = 'open'
        task2.save()

        # Task in progress, don't count
        TaskMemberFactory(task=task3, status='accepted')
        task3.status = 'in_progress'
        task3.save()

        self.assertEquals(
            self.metrics.calculate_realized_tasks_unconfirmed_taskmembers(), 1)

    def test_tasks_with_realized_taskmember(self):
        """ Test task counting with realized task members """

        # Task can be any status
        task1 = TaskFactory(status='realized')
        task2 = TaskFactory(status='realized')
        task3 = TaskFactory(status='in_progress')

        TaskMemberFactory(task=task1, status='realized')
        TaskMemberFactory(task=task1, status='applied')

        # Don't count task twice
        TaskMemberFactory(task=task2, status='realized')
        TaskMemberFactory(task=task2, status='realized')

        TaskMemberFactory(task=task3, status='realized')
        TaskMemberFactory(task=task3, status='applied')

        self.assertEquals(self.metrics.calculate_tasks_realized_taskmembers(), 3)
