# -*- coding: utf-8 -*-
from datetime import timedelta

from django.core import mail
from django.utils.timezone import now
from moneyed import Money

from bluebottle.funding.tasks import check_funding_end
from bluebottle.funding.tests.factories import FundingFactory, DonationFactory, \
    BudgetLineFactory, BankAccountFactory
from bluebottle.funding.transitions import DonationTransitions
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class FundingTestCase(BluebottleAdminTestCase):
    def setUp(self):
        super(FundingTestCase, self).setUp()
        user = BlueBottleUserFactory.create(first_name='Jean Baptiste')
        self.initiative = InitiativeFactory.create(activity_manager=user)
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.initiative.save()
        self.funding = FundingFactory.create(
            owner=user,
            initiative=self.initiative,
            target=Money(500, 'EUR'),
            deadline=now() + timedelta(weeks=2),
            bank_account=BankAccountFactory.create()
        )
        BudgetLineFactory.create(activity=self.funding)
        self.funding.bank_account.reviewed = True

        self.funding.review_transitions.submit()
        self.funding.review_transitions.approve()
        BudgetLineFactory.create_batch(4, activity=self.funding, amount=Money(125, 'EUR'))
        mail.outbox = []

    def test_approve_deadline(self):
        funding = FundingFactory.create(
            owner=self.initiative.activity_manager,
            initiative=self.initiative,
            target=Money(500, 'EUR'),
            duration=30,
            deadline=None,
            bank_account=BankAccountFactory.create()
        )
        BudgetLineFactory.create(activity=funding)
        funding.bank_account.reviewed = True

        funding.review_transitions.submit()
        funding.review_transitions.approve()

        self.assertAlmostEqual(
            funding.deadline,
            (now() + timedelta(days=30)).replace(hour=23, minute=59, second=59),
            delta=timedelta(seconds=1)
        )

    def test_no_donations(self):
        self.assertEqual(self.funding.initiative.status, 'approved')
        self.assertEqual(self.funding.status, 'open')
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()
        check_funding_end()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'closed')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your crowdfunding campaign has been closed')
        self.assertTrue('Hi Jean Baptiste,' in mail.outbox[0].body)

    def test_some_donations(self):
        user = BlueBottleUserFactory.create(first_name='Bill')
        donation = DonationFactory.create(
            user=user,
            activity=self.funding,
            amount=Money(50, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(donation.status, DonationTransitions.values.succeeded)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].subject, u'You have a new donation!💰')
        self.assertEqual(mail.outbox[1].subject, 'Thanks for your donation!')
        self.assertTrue('Hi Jean Baptiste,' in mail.outbox[0].body)
        self.assertTrue('Hi Bill,' in mail.outbox[1].body)

        # Donation amount should appear in both emails
        self.assertTrue(u'€ 50' in mail.outbox[0].body)
        self.assertTrue(u'€ 50' in mail.outbox[1].body)

        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()

        # Run scheduled task
        check_funding_end()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'partially_funded')
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(mail.outbox[2].subject, 'Your crowdfunding campaign deadline passed')
        self.assertTrue('Hi Jean Baptiste,' in mail.outbox[0].body)

    def test_enough_donations(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(300, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        donation = DonationFactory.create(activity=self.funding, amount=Money(450, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(len(mail.outbox), 4)
        self.assertEqual(donation.status, 'succeeded')
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()

        # Run scheduled task
        check_funding_end()
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(mail.outbox[4].subject, u'You successfully completed your crowdfunding campaign! 🎉')
        self.assertTrue('Hi Jean Baptiste,' in mail.outbox[4].body)
