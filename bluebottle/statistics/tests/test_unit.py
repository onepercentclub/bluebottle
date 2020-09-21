import datetime

from builtins import range
from django.test.utils import override_settings
from django.utils import timezone
from moneyed.classes import Money

from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.funding.tests.factories import (
    FundingFactory, DonationFactory, BankAccountFactory, BudgetLineFactory, PlainPayoutAccountFactory
)
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import Member
from bluebottle.statistics.statistics import Statistics
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class InitialStatisticsTest(BluebottleTestCase):
    def setUp(self):
        super(InitialStatisticsTest, self).setUp()
        self.stats = Statistics()
        Member.objects.all().delete()

        self.some_user = BlueBottleUserFactory.create()

        self.some_initiative = InitiativeFactory.create(
            owner=self.some_user
        )

    def test_initial_stats(self):
        self.assertEqual(self.stats.activities_online, 0)
        self.assertEqual(self.stats.activities_succeeded, 0)
        self.assertEqual(self.stats.assignments_succeeded, 0)
        self.assertEqual(self.stats.events_succeeded, 0)
        self.assertEqual(self.stats.fundings_succeeded, 0)
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
        Member.objects.all().delete()

        self.some_user = BlueBottleUserFactory.create()
        self.other_user = BlueBottleUserFactory.create()

        self.initiative = InitiativeFactory.create(
            owner=self.some_user
        )
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)


class EventStatisticsTest(StatisticsTest):
    def setUp(self):
        super(EventStatisticsTest, self).setUp()
        self.event = EventFactory.create(
            initiative=self.initiative,
            owner=self.some_user,
            capacity=10,
            duration=0.1
        )
        self.event.states.submit(save=True)

    def test_open(self):
        self.assertEqual(
            self.stats.activities_online, 1
        )
        self.assertEqual(
            self.stats.activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.events_succeeded, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_succeeded(self):
        self.event.states.succeed(save=True)
        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.events_succeeded, 1
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_closed(self):
        self.event.states.cancel(save=True)

        self.initiative.save()
        self.event.save()

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.events_succeeded, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_participant(self):
        ParticipantFactory.create(activity=self.event, user=self.other_user)
        self.event.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.events_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_spent, 0.1
        )
        self.assertEqual(
            self.stats.event_members, 1
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_participant_withdrawn(self):
        contribution = ParticipantFactory.create(activity=self.event, user=self.other_user)
        contribution.states.withdraw(save=True)
        self.event.states.start(save=True)
        self.event.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.events_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_spent, 0
        )
        self.assertEqual(
            self.stats.event_members, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_participant_noshow(self):
        contribution = ParticipantFactory.create(activity=self.event, user=self.other_user)
        self.event.states.start(save=True)
        self.event.states.succeed(save=True)
        contribution.states.succeed(save=True)
        contribution.states.mark_absent(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.events_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_spent, 0
        )
        self.assertEqual(
            self.stats.event_members, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )


class AssignmentStatisticsTest(StatisticsTest):
    def setUp(self):
        super(AssignmentStatisticsTest, self).setUp()
        self.assignment = AssignmentFactory.create(
            owner=self.some_user,
            initiative=self.initiative,
            registration_deadline=(timezone.now() + datetime.timedelta(hours=24)).date(),
            date=(timezone.now() + datetime.timedelta(hours=48)),
            duration=0.1
        )
        self.assignment.states.submit(save=True)

    def test_open(self):
        self.assertEqual(
            self.stats.activities_online, 1
        )
        self.assertEqual(
            self.stats.activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.assignments_succeeded, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_succeeded(self):
        self.assignment.states.start(save=True)
        self.assignment.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.assignments_succeeded, 1
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_cancelled(self):
        self.assignment.states.start(save=True)
        self.assignment.states.cancel(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.assignments_succeeded, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_applicant(self):
        contribution = ApplicantFactory.create(activity=self.assignment, user=self.other_user)
        contribution.states.accept(save=True)
        self.assignment.states.start(save=True)
        self.assignment.states.succeed(save=True)
        contribution.refresh_from_db()
        contribution.time_spent = 32
        contribution.save()
        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.assignments_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_spent, 32
        )
        self.assertEqual(
            self.stats.assignment_members, 1
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_applicant_withdrawn(self):
        contribution = ApplicantFactory.create(activity=self.assignment, user=self.other_user)
        contribution.states.withdraw(save=True)
        self.assignment.states.start(save=True)
        self.assignment.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.assignments_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_spent, 0
        )
        self.assertEqual(
            self.stats.assignment_members, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_participant_rejected(self):
        contribution = ApplicantFactory.create(activity=self.assignment, user=self.other_user)
        contribution.states.reject(save=True)
        self.assignment.states.start(save=True)
        self.assignment.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.assignments_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_spent, 0
        )
        self.assertEqual(
            self.stats.assignment_members, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )


class FundingStatisticsTest(StatisticsTest):
    def setUp(self):
        super(FundingStatisticsTest, self).setUp()
        payout_account = PlainPayoutAccountFactory.create()
        bank_account = BankAccountFactory.create(connect_account=payout_account)
        self.funding = FundingFactory.create(
            owner=self.some_user,
            bank_account=bank_account,
            initiative=self.initiative,
            target=Money(100, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        self.funding.states.submit()
        self.funding.states.approve(save=True)

    def test_open(self):
        self.assertEqual(
            self.stats.activities_online, 1
        )
        self.assertEqual(
            self.stats.activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.fundings_succeeded, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_succeeded(self):
        self.funding.states.succeed(save=True)
        self.funding.amount_matching = Money(100, 'EUR')
        self.funding.save()

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.fundings_succeeded, 1
        )
        self.assertEqual(
            self.stats.amount_matched, Money(100, 'EUR')
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_closed(self):
        self.funding.states.cancel(save=True)
        self.funding.amount_matching = Money(100, 'EUR')
        self.funding.save()

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.fundings_succeeded, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )
        self.assertEqual(
            self.stats.amount_matched, Money(0, 'EUR')
        )

    def test_donation(self):
        self.funding.states.succeed(save=True)

        contribution = DonationFactory.create(
            activity=self.funding,
            user=self.other_user,
            amount=Money(50, 'EUR')
        )
        contribution.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.fundings_succeeded, 1
        )
        self.assertEqual(
            self.stats.donated_total, Money(50, 'EUR')
        )
        self.assertEqual(
            self.stats.donations, 1
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_donation_many(self):
        self.funding.states.succeed(save=True)

        for i in range(4):
            contribution = DonationFactory.create(
                activity=self.funding,
                user=self.other_user,
                amount=Money(50, 'EUR')
            )
            contribution.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.fundings_succeeded, 1
        )
        self.assertEqual(
            self.stats.donated_total, Money(200, 'EUR')
        )
        self.assertEqual(
            self.stats.donations, 4
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_pledge(self):
        self.funding.states.succeed(save=True)

        contribution = DonationFactory.create(
            activity=self.funding,
            user=self.other_user,
            amount=Money(50, 'EUR')
        )
        PledgePaymentFactory.create(
            donation=contribution
        )

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.fundings_succeeded, 1
        )
        self.assertEqual(
            self.stats.pledged_total, Money(50, 'EUR')
        )
        self.assertEqual(
            self.stats.donated_total, Money(50, 'EUR')
        )
        self.assertEqual(
            self.stats.donations, 1
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_donation_other_currency(self):
        self.funding.states.succeed(save=True)

        contribution = DonationFactory.create(
            activity=self.funding,
            user=self.other_user,
            amount=Money(50, 'USD')
        )
        contribution.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.fundings_succeeded, 1
        )
        self.assertEqual(
            self.stats.donated_total, Money(75, 'EUR')
        )
        self.assertEqual(
            self.stats.donations, 1
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_donation_multiple_currencies(self):
        self.funding.states.succeed(save=True)

        for currency in ('EUR', 'USD'):
            contribution = DonationFactory.create(
                activity=self.funding,
                user=self.other_user,
                amount=Money(50, currency)
            )
            contribution.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.fundings_succeeded, 1
        )
        self.assertEqual(
            self.stats.donated_total, Money(125, 'EUR')
        )
        self.assertEqual(
            self.stats.donations, 2
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_donation_failed(self):
        contribution = DonationFactory.create(
            activity=self.funding,
            user=self.other_user,
            amount=Money(50, 'EUR')
        )
        contribution.states.fail(save=True)
        self.funding.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.fundings_succeeded, 1
        )
        self.assertEqual(
            self.stats.donated_total, Money(0, 'EUR')
        )
        self.assertEqual(
            self.stats.donations, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )


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

        user = BlueBottleUserFactory.create()
        other_user = BlueBottleUserFactory.create()

        for diff in (10, 5, 1):
            initiative = InitiativeFactory.create(owner=user)
            past_date = timezone.now() - datetime.timedelta(days=diff)
            initiative.created = past_date
            initiative.save()
            initiative.states.submit()
            initiative.states.approve(save=True)

            event = EventFactory(
                start=past_date,
                initiative=initiative,
                duration=1,
                transition_date=past_date,
                status='succeeded',
                owner=BlueBottleUserFactory.create(),
            )

            ParticipantFactory.create(
                activity=event,
                status='succeeded',
                time_spent=1,
                user=other_user
            )

    def test_all(self):
        stats = Statistics()
        self.assertEqual(
            stats.activities_succeeded, 3
        )
        self.assertEqual(
            stats.events_succeeded, 3
        )
        self.assertEqual(
            stats.people_involved, 5
        )

    def test_end(self):
        stats = Statistics(end=timezone.now() - datetime.timedelta(days=2))
        self.assertEqual(
            stats.activities_succeeded, 2
        )
        self.assertEqual(
            stats.events_succeeded, 2
        )
        self.assertEqual(
            stats.people_involved, 2
        )

    def test_start(self):
        stats = Statistics(start=timezone.now() - datetime.timedelta(days=9))
        self.assertEqual(
            stats.activities_succeeded, 2
        )
        self.assertEqual(
            stats.events_succeeded, 2
        )

        self.assertEqual(
            stats.people_involved, 5
        )

    def test_both(self):
        stats = Statistics(
            start=timezone.now() - datetime.timedelta(days=9),
            end=timezone.now() - datetime.timedelta(days=2)
        )
        self.assertEqual(
            stats.activities_succeeded, 1
        )
        self.assertEqual(
            stats.events_succeeded, 1
        )
        self.assertEqual(
            stats.people_involved, 2
        )
