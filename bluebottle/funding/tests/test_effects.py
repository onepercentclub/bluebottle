from datetime import timedelta

from django.utils.timezone import now
from djmoney.money import Money

from bluebottle.funding.effects import GeneratePayoutsEffect, DeletePayoutsEffect, UpdateFundingAmountsEffect, \
    SetDeadlineEffect, GenerateDonationWallpostEffect, RemoveDonationWallpostEffect, \
    SubmitConnectedActivitiesEffect, SetDateEffect, ClearPayoutDatesEffect
from bluebottle.funding.tests.factories import FundingFactory, BudgetLineFactory, BankAccountFactory, \
    PlainPayoutAccountFactory, DonationFactory, PayoutFactory
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.wallposts.models import Wallpost


class FundingEffectsTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.payout_account = PlainPayoutAccountFactory.create(
            status='verified'
        )
        bank_account = BankAccountFactory.create(connect_account=self.payout_account)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR'),
            duration=30,
            bank_account=bank_account
        )
        BudgetLineFactory.create(activity=self.funding)
        self.funding.states.submit(save=True)
        self.donation = DonationFactory.create(
            activity=self.funding,
            amount=Money(100, 'EUR'),
            status='succeeded'
        )
        PledgePaymentFactory.create(donation=self.donation)

    def test_generate_payouts_effect(self):
        effect = GeneratePayoutsEffect(self.funding)
        self.assertEqual(unicode(effect), 'Generate payouts, so that payouts can be approved')
        effect.execute()
        self.assertEqual(self.funding.payouts.count(), 1)

    def test_delete_payouts_effect(self):
        PayoutFactory.create(activity=self.funding)
        effect = DeletePayoutsEffect(self.funding)
        self.assertEqual(unicode(effect), 'Delete all related payouts')
        effect.execute()
        self.assertEqual(self.funding.payouts.count(), 0)

    def test_update_funding_amounts_effect(self):
        effect = UpdateFundingAmountsEffect(self.donation)
        self.assertEqual(unicode(effect), 'Update total amounts')
        effect.execute()
        self.assertEqual(self.funding.amount_donated, Money(100, 'EUR'))

    def test_set_deadline_effect(self):
        self.funding.deadline = None
        self.funding.save()
        self.assertIsNone(self.funding.deadline)
        effect = SetDeadlineEffect(self.funding)
        self.assertEqual(unicode(effect), 'Set deadline according to the duration')
        effect.execute()
        self.assertIsNotNone(self.funding.deadline)

    def test_generate_donation_wallpost_effect(self):
        PayoutFactory.create(activity=self.funding)
        effect = GenerateDonationWallpostEffect(self.donation)
        self.assertEqual(unicode(effect), 'Generate wallpost for donation')
        effect.execute()
        self.assertEqual(Wallpost.objects.count(), 1)

    def test_remove_donation_wallpost_effect(self):
        PayoutFactory.create(activity=self.funding)
        effect = GenerateDonationWallpostEffect(self.donation)
        effect.execute()
        self.assertEqual(Wallpost.objects.count(), 1)
        effect = RemoveDonationWallpostEffect(self.donation)
        self.assertEqual(unicode(effect), 'Delete wallpost for donation')
        effect.execute()
        self.assertEqual(Wallpost.objects.count(), 0)

    def test_submit_connected_activities_effect(self):
        self.funding.status = 'draft'
        self.funding.save()
        effect = SubmitConnectedActivitiesEffect(self.payout_account)
        self.assertEqual(unicode(effect), 'Submit connected activities')
        effect.execute()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'submitted')

    def test_set_date_effect(self):
        effect = SetDateEffect('started')(self.funding)
        self.assertEqual(unicode(effect), 'Set started to current date')
        effect.execute()
        self.funding.refresh_from_db()
        self.assertAlmostEqual(self.funding.created, now(), delta=timedelta(seconds=60))

    def test_clear_payout_dates_effect(self):
        payout = PayoutFactory.create(
            date_approved=now(),
            date_started=now(),
            date_completed=now(),
        )
        self.assertIsNotNone(payout.date_approved)
        effect = ClearPayoutDatesEffect(payout)
        self.assertEqual(unicode(effect), 'Clear payout event dates')
        effect.execute()
        self.assertIsNone(payout.date_approved)
        self.assertIsNone(payout.date_started)
        self.assertIsNone(payout.date_completed)
