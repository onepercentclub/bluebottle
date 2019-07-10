from datetime import timedelta

from django.utils.timezone import now
from moneyed import Money

from bluebottle.funding.tasks import check_funding_end
from bluebottle.funding.tests.factories import FundingFactory, DonationFactory, \
    BudgetLineFactory
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class FundingTaskTestCase(BluebottleAdminTestCase):
    def setUp(self):
        super(FundingTaskTestCase, self).setUp()
        self.initiative = InitiativeFactory.create()
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.initiative.save()
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(500, 'EUR'),
            deadline=(now() + timedelta(weeks=2)).date()
        )
        BudgetLineFactory.create_batch(4, activity=self.funding, amount=Money(125, 'EUR'))

    def test_no_donations(self):
        self.assertEqual(self.funding.initiative.status, 'approved')
        self.assertEqual(self.funding.status, 'open')
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()
        check_funding_end()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'closed')

    def test_some_donations(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(50, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(donation.status, 'succeeded')
        self.funding.deadline = (now() - timedelta(days=1)).date()
        self.funding.save()

        # Run scheduled task
        check_funding_end()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'partially_funded')

    def test_enough_donations(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(300, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        donation = DonationFactory.create(activity=self.funding, amount=Money(450, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(donation.status, 'succeeded')
        self.funding.deadline = (now() - timedelta(days=1)).date()
        self.funding.save()

        # Run scheduled task
        check_funding_end()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'succeeded')

    def test_extending(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(100, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(donation.status, 'succeeded')
        self.funding.deadline = (now() - timedelta(days=1)).date()
        self.funding.save()

        # Run scheduled task
        check_funding_end()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'partially_funded')

        # Extend the campaign
        self.funding.deadline = (now() + timedelta(weeks=2)).date()
        self.funding.transitions.close()
        self.funding.transitions.extend()
        self.funding.save()
        donation = DonationFactory.create(activity=self.funding, amount=Money(700, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.funding.deadline = (now() - timedelta(days=1)).date()
        self.funding.save()

        # Run scheduled task
        check_funding_end()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'succeeded')
