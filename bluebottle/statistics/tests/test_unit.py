
import datetime

from django.test.utils import override_settings
from django.utils import timezone
from moneyed.classes import Money

from bluebottle.members.models import Member
from bluebottle.statistics.views import Statistics
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.funding.tests.factories import (
    FundingFactory, DonationFactory, BankAccountFactory, BudgetLineFactory
)
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
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


class EventStatisticsTest(StatisticsTest):
    def setUp(self):
        super(EventStatisticsTest, self).setUp()
        self.event = EventFactory.create(
            owner=self.some_user,
            initiative=self.initiative,
            start_date=timezone.now() - datetime.timedelta(hours=1),
            duration=0.1
        )

    def test_open(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.event.review_transitions.submit()

        self.initiative.save()
        self.event.save()

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
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.event.review_transitions.submit()
        self.event.transitions.start()
        self.event.transitions.succeed()

        self.initiative.save()
        self.event.save()

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
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.event.review_transitions.submit()
        self.event.transitions.start()
        self.event.transitions.succeed()
        self.event.transitions.close()

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
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.event.review_transitions.submit()
        ParticipantFactory.create(activity=self.event, user=self.other_user)
        self.event.transitions.start()
        self.event.transitions.succeed()

        self.initiative.save()
        self.event.save()

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
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.event.review_transitions.submit()
        contribution = ParticipantFactory.create(activity=self.event, user=self.other_user)
        contribution.transitions.withdraw()
        contribution.save()
        self.event.transitions.start()
        self.event.transitions.succeed()

        self.initiative.save()
        self.event.save()

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
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.event.review_transitions.submit()
        contribution = ParticipantFactory.create(activity=self.event, user=self.other_user)
        self.event.transitions.start()
        self.event.transitions.succeed()
        contribution.transitions.succeed()
        contribution.transitions.no_show()
        contribution.save()

        self.initiative.save()
        self.event.save()

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
            end_date=(timezone.now() + datetime.timedelta(hours=48)).date(),
            duration=0.1
        )

    def test_open(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.assignment.review_transitions.submit()

        self.initiative.save()
        self.assignment.save()

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
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.assignment.review_transitions.submit()
        self.assignment.transitions.start()
        self.assignment.transitions.succeed()

        self.initiative.save()
        self.assignment.save()

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

    def test_closed(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.assignment.review_transitions.submit()
        self.assignment.transitions.start()
        self.assignment.transitions.succeed()
        self.assignment.transitions.close()

        self.initiative.save()
        self.assignment.save()

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

    def test_participant(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.assignment.review_transitions.submit()
        contribution = ApplicantFactory.create(activity=self.assignment, user=self.other_user)
        contribution.transitions.accept()
        contribution.save()
        self.assignment.transitions.start()
        self.assignment.transitions.succeed()
        contribution.refresh_from_db()
        contribution.time_spent = 0.1
        contribution.save()

        self.initiative.save()
        self.assignment.save()

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
            self.stats.time_spent, 0.1
        )
        self.assertEqual(
            self.stats.assignment_members, 1
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_participant_withdrawn(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.assignment.review_transitions.submit()
        contribution = ApplicantFactory.create(activity=self.assignment, user=self.other_user)
        contribution.transitions.withdraw()
        contribution.save()
        self.assignment.transitions.start()
        self.assignment.transitions.succeed()

        self.initiative.save()
        self.assignment.save()

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
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.assignment.review_transitions.submit()
        contribution = ApplicantFactory.create(activity=self.assignment, user=self.other_user)
        contribution.transitions.reject()
        self.assignment.transitions.start()
        self.assignment.transitions.succeed()
        contribution.save()

        self.initiative.save()
        self.assignment.save()

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
        self.funding = FundingFactory.create(
            owner=self.some_user,
            bank_account=BankAccountFactory.create(),
            initiative=self.initiative,
            target=Money(100, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)

    def test_open(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.funding.review_transitions.submit()
        self.funding.review_transitions.approve()

        self.initiative.save()
        self.funding.save()

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
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.funding.review_transitions.submit()
        self.funding.review_transitions.approve()
        self.funding.transitions.succeed()

        self.initiative.save()
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
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.funding.review_transitions.submit()
        self.funding.review_transitions.approve()
        self.funding.transitions.succeed()
        self.funding.transitions.close()

        self.initiative.save()
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
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.funding.review_transitions.submit()
        self.funding.review_transitions.approve()
        self.funding.transitions.succeed()

        contribution = DonationFactory.create(
            activity=self.funding,
            user=self.other_user,
            amount=Money(50, 'EUR')
        )
        contribution.transitions.succeed()
        contribution.save()

        self.initiative.save()
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
            self.stats.donated_total, Money(50, 'EUR')
        )
        self.assertEqual(
            self.stats.donations, 1
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_donation_many(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.funding.review_transitions.submit()
        self.funding.review_transitions.approve()
        self.funding.transitions.succeed()

        for i in range(4):
            contribution = DonationFactory.create(
                activity=self.funding,
                user=self.other_user,
                amount=Money(50, 'EUR')
            )
            contribution.transitions.succeed()
            contribution.save()

        self.initiative.save()
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
            self.stats.donated_total, Money(200, 'EUR')
        )
        self.assertEqual(
            self.stats.donations, 4
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_pledge(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.funding.review_transitions.submit()
        self.funding.review_transitions.approve()
        self.funding.transitions.succeed()

        contribution = DonationFactory.create(
            activity=self.funding,
            user=self.other_user,
            amount=Money(50, 'EUR')
        )
        PledgePaymentFactory.create(
            donation=contribution
        )
        contribution.save()

        self.initiative.save()
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
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.funding.review_transitions.submit()
        self.funding.review_transitions.approve()
        self.funding.transitions.succeed()

        contribution = DonationFactory.create(
            activity=self.funding,
            user=self.other_user,
            amount=Money(50, 'USD')
        )
        contribution.transitions.succeed()
        contribution.save()

        self.initiative.save()
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
            self.stats.donated_total, Money(75, 'EUR')
        )
        self.assertEqual(
            self.stats.donations, 1
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_donation_multiple_currencies(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.funding.review_transitions.submit()
        self.funding.review_transitions.approve()
        self.funding.transitions.succeed()

        for currency in ('EUR', 'USD'):
            contribution = DonationFactory.create(
                activity=self.funding,
                user=self.other_user,
                amount=Money(50, currency)
            )
            contribution.transitions.succeed()
            contribution.save()

        self.initiative.save()
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
            self.stats.donated_total, Money(125, 'EUR')
        )
        self.assertEqual(
            self.stats.donations, 2
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_donation_failed(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.funding.review_transitions.submit()
        self.funding.review_transitions.approve()

        contribution = DonationFactory.create(
            activity=self.funding,
            user=self.other_user,
            amount=Money(50, 'EUR')
        )

        contribution.transitions.fail()
        contribution.save()

        self.funding.transitions.succeed()

        self.initiative.save()
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
            initiative = InitiativeFactory.create(status='approved', owner=user)

            past_date = timezone.now() - datetime.timedelta(days=diff)
            initiative.created = past_date
            initiative.save()

            event = EventFactory(status='succeeded', transition_date=past_date)

            ParticipantFactory.create(
                status='succeeded',
                activity=event,
                transition_date=past_date,
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
            stats.people_involved, 2
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
            stats.people_involved, 2
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
