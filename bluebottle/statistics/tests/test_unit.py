import datetime
from builtins import range
from datetime import timedelta

from django.test.utils import override_settings
from django.utils import timezone
from django.utils.timezone import now
from moneyed.classes import Money

from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.funding.tests.factories import (
    FundingFactory, DonorFactory, BankAccountFactory, BudgetLineFactory, PlainPayoutAccountFactory
)
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import Member
from bluebottle.statistics.statistics import Statistics
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, DateParticipantFactory,
    PeriodActivityFactory, PeriodParticipantFactory, DateActivitySlotFactory
)


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
        self.assertEqual(self.stats.time_activities_succeeded, 0)
        self.assertEqual(self.stats.fundings_succeeded, 0)
        self.assertEqual(self.stats.deeds_succeeded, 0)
        self.assertEqual(self.stats.people_involved, 0)
        self.assertEqual(self.stats.donated_total, Money(0, 'EUR'))
        self.assertEqual(self.stats.deeds_done, 0)


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


class DateActivityStatisticsTest(StatisticsTest):
    def setUp(self):
        super(DateActivityStatisticsTest, self).setUp()
        self.activity = DateActivityFactory.create(
            initiative=self.initiative,
            preparation=None,
            owner=self.some_user,
            capacity=10,
            slots=[]
        )
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity,
            start=now() + timedelta(days=2),
            duration=timedelta(minutes=90)
        )
        self.activity.states.publish(save=True)

    def test_open(self):
        self.assertEqual(
            self.stats.activities_online, 1
        )
        self.assertEqual(
            self.stats.activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.time_activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_succeeded(self):
        self.activity.states.succeed(save=True)
        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_closed(self):
        self.activity.states.cancel(save=True)

        self.initiative.save()
        self.activity.save()

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.time_activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_participant(self):
        DateParticipantFactory.create(activity=self.activity, user=self.other_user)
        self.activity.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_spent, 1.5
        )
        self.assertEqual(
            self.stats.activity_participants, 1
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_participant_withdrawn(self):
        contribution = DateParticipantFactory.create(activity=self.activity, user=self.other_user)
        contribution.states.withdraw(save=True)
        self.activity.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_spent, 0
        )
        self.assertEqual(
            self.stats.activity_participants, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_participant_noshow(self):
        participant = DateParticipantFactory.create(activity=self.activity, user=self.other_user)
        self.activity.states.succeed(save=True)
        participant.states.remove(save=True)
        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_spent, 0
        )
        self.assertEqual(
            self.stats.activity_participants, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )


class PeriodActivityStatisticsTest(StatisticsTest):
    def setUp(self):
        super(PeriodActivityStatisticsTest, self).setUp()
        self.activity = PeriodActivityFactory.create(
            owner=self.some_user,
            initiative=self.initiative,
            registration_deadline=(timezone.now() + datetime.timedelta(hours=24)).date(),
            deadline=datetime.date.today() + datetime.timedelta(days=48),
            duration=datetime.timedelta(minutes=6)
        )
        self.activity.states.publish(save=True)

    def test_open(self):
        self.assertEqual(
            self.stats.activities_online, 1
        )
        self.assertEqual(
            self.stats.activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_succeeded(self):
        self.activity.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_cancelled(self):
        self.activity.states.cancel(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.time_activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_applicant(self):
        contributor = PeriodParticipantFactory.create(activity=self.activity, user=self.other_user)
        self.activity.states.succeed(save=True)
        contributor.refresh_from_db()
        contribution = contributor.contributions.get()
        contribution.value = datetime.timedelta(hours=4)

        contribution.save()
        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_spent, 4.0
        )
        self.assertEqual(
            self.stats.time_activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_applicant_withdrawn(self):
        contribution = PeriodParticipantFactory.create(activity=self.activity, user=self.other_user)
        contribution.states.withdraw(save=True)
        self.activity.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_spent, 0
        )
        self.assertEqual(
            self.stats.time_activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_participant_rejected(self):
        contribution = PeriodParticipantFactory.create(activity=self.activity, user=self.other_user)
        contribution.states.remove(save=True)
        self.activity.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.time_spent, 0
        )
        self.assertEqual(
            self.stats.time_activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )


class FundingStatisticsTest(StatisticsTest):
    def setUp(self):
        super(FundingStatisticsTest, self).setUp()
        payout_account = PlainPayoutAccountFactory.create()
        bank_account = BankAccountFactory.create(connect_account=payout_account, status='verified')
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
        self.funding.amount_matching = Money(100, 'EUR')
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
        self.assertEqual(
            self.stats.amount_matched, Money(100, 'EUR')
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

        contribution = DonorFactory.create(
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
            contribution = DonorFactory.create(
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

        contribution = DonorFactory.create(
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

        contribution = DonorFactory.create(
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
            contribution = DonorFactory.create(
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
        contribution = DonorFactory.create(
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
class DeedStatisticsTest(StatisticsTest):
    def setUp(self):
        super(DeedStatisticsTest, self).setUp()
        self.activity = DeedFactory.create(
            initiative=self.initiative,
            owner=self.some_user,
            start=datetime.date.today() + datetime.timedelta(days=5),
            end=datetime.date.today() + datetime.timedelta(days=10)
        )
        self.activity.states.publish(save=True)

    def test_open(self):
        self.assertEqual(
            self.stats.activities_online, 1
        )
        self.assertEqual(
            self.stats.activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.deeds_succeeded, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_succeeded(self):
        self.activity.states.succeed(save=True)
        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.deeds_succeeded, 1
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_closed(self):
        self.activity.states.cancel(save=True)

        self.initiative.save()
        self.activity.save()

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 0
        )
        self.assertEqual(
            self.stats.deeds_succeeded, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_participant(self):
        DeedParticipantFactory.create(activity=self.activity, user=self.other_user)
        self.activity.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.deeds_succeeded, 1
        )
        self.assertEqual(
            self.stats.deeds_done, 1
        )
        self.assertEqual(
            self.stats.people_involved, 2
        )

    def test_participant_withdrawn(self):
        contribution = DeedParticipantFactory.create(activity=self.activity, user=self.other_user)
        contribution.states.withdraw(save=True)
        self.activity.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.deeds_succeeded, 1
        )
        self.assertEqual(
            self.stats.deeds_done, 0
        )
        self.assertEqual(
            self.stats.people_involved, 1
        )

    def test_participant_noshow(self):
        DeedParticipantFactory.create(activity=self.activity, user=self.other_user)
        contribution = DeedParticipantFactory.create(activity=self.activity, user=self.other_user)
        contribution.states.remove(save=True)
        self.activity.states.succeed(save=True)

        self.assertEqual(
            self.stats.activities_online, 0
        )
        self.assertEqual(
            self.stats.activities_succeeded, 1
        )
        self.assertEqual(
            self.stats.deeds_succeeded, 1
        )
        self.assertEqual(
            self.stats.deeds_done, 1
        )
        self.assertEqual(
            self.stats.people_involved, 2
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

            activity = DateActivityFactory(
                initiative=initiative,
                transition_date=past_date,
                owner=BlueBottleUserFactory.create(),
                slots=[]
            )
            DateActivitySlotFactory.create(
                activity=activity,
                start=past_date,
                duration=datetime.timedelta(minutes=60),
            )

            DateParticipantFactory.create(
                activity=activity,
                user=other_user
            )
            activity.states.publish(save=True)

    def test_all(self):
        stats = Statistics()
        self.assertEqual(
            stats.activities_succeeded, 3
        )
        self.assertEqual(
            stats.time_activities_succeeded, 3
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
            stats.time_activities_succeeded, 2
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
            stats.time_activities_succeeded, 2
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
            stats.time_activities_succeeded, 1
        )
        self.assertEqual(
            stats.people_involved, 2
        )
