# -*- coding: utf-8 -*-
from datetime import timedelta, datetime

from django.core import mail
from django.db import connection
from django.utils.timezone import now, get_current_timezone
from moneyed import Money

from bluebottle.activities.models import Organizer
from bluebottle.clients.utils import LocalTenant
from bluebottle.fsm import TransitionNotPossible
from bluebottle.funding.tasks import check_funding_end
from bluebottle.funding.tests.factories import FundingFactory, DonationFactory, \
    BudgetLineFactory, BankAccountFactory, PlainPayoutAccountFactory
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class FundingTestCase(BluebottleAdminTestCase):
    def setUp(self):
        super(FundingTestCase, self).setUp()
        user = BlueBottleUserFactory.create(first_name='Jean Baptiste')
        self.initiative = InitiativeFactory.create(activity_manager=user)
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            owner=user,
            initiative=self.initiative,
            target=Money(500, 'EUR'),
            deadline=now() + timedelta(weeks=2),
            bank_account=BankAccountFactory.create()
        )
        BudgetLineFactory.create(activity=self.funding)
        self.funding.bank_account.reviewed = True

        self.funding.states.approve()
        BudgetLineFactory.create_batch(4, activity=self.funding, amount=Money(125, 'EUR'))
        mail.outbox = []

    def test_default_status(self):
        self.assertEqual(self.funding.status, self.funding.states.open.value)
        organizer = self.funding.contributions.instance_of(Organizer).get()
        self.assertEqual(organizer.status, organizer.states.new.value)
        self.assertEqual(organizer.user, self.funding.owner)

    def test_review(self):
        funding = FundingFactory.create(initiative=self.initiative)
        self.assertEqual(funding.status, funding.states.draft.value)
        BudgetLineFactory.create(activity=funding)
        payout_account = PlainPayoutAccountFactory.create()
        bank_account = BankAccountFactory.create(connect_account=payout_account)
        funding.bank_account = bank_account
        funding.save()
        self.assertEqual(funding.status, funding.states.submitted.value)
        organizer = funding.contributions.instance_of(Organizer).get()
        self.assertEqual(organizer.status, organizer.states.new.value)
        self.assertEqual(organizer.user, funding.owner)

    def test_approve_deadline(self):
        funding = FundingFactory.create(
            owner=self.initiative.activity_manager,
            initiative=self.initiative,
            target=Money(500, 'EUR'),
            duration=30,
            deadline=None,
            bank_account=BankAccountFactory.create()
        )

        self.assertIsNone(funding.started)

        BudgetLineFactory.create(activity=funding)
        funding.bank_account.reviewed = True

        funding.states.approve(save=True)

        self.assertIsInstance(funding.started, datetime)

        deadline = now() + timedelta(days=30)
        self.assertAlmostEqual(
            funding.deadline,
            get_current_timezone().localize(
                datetime(
                    deadline.year,
                    deadline.month,
                    deadline.day,
                    hour=23,
                    minute=59,
                    second=59
                )
            ),
            delta=timedelta(seconds=1)
        )

    def test_no_donations(self):
        self.assertEqual(self.funding.initiative.status, 'approved')
        self.assertEqual(self.funding.status, 'open')
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()

        # Run scheduled task
        tenant = connection.tenant
        check_funding_end()
        with LocalTenant(tenant, clear_tenant=True):
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
        donation.states.succeed(save=True)
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(donation.status, donation.states.succeeded.value)
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
        tenant = connection.tenant
        check_funding_end()
        with LocalTenant(tenant, clear_tenant=True):
            self.funding.refresh_from_db()

        self.assertEqual(self.funding.status, 'partially_funded')
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(mail.outbox[2].subject, 'Your crowdfunding campaign deadline passed')
        self.assertTrue('Hi Jean Baptiste,' in mail.outbox[0].body)
        url = 'http://testserver/en/initiatives/activities/details/funding/{}/{}'.format(
            self.funding.id, self.funding.slug
        )
        self.assertTrue(url in mail.outbox[0].body)

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
        tenant = connection.tenant
        check_funding_end()
        with LocalTenant(tenant, clear_tenant=True):
            self.funding.refresh_from_db()

        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(mail.outbox[4].subject, u'You successfully completed your crowdfunding campaign! 🎉')
        self.assertTrue('Hi Jean Baptiste,' in mail.outbox[4].body)
        url = 'http://testserver/en/initiatives/activities/details/funding/{}/{}'.format(
            self.funding.id, self.funding.slug
        )
        self.assertTrue(url in mail.outbox[4].body)

        organizer = self.funding.contributions.instance_of(Organizer).get()
        self.assertEqual(organizer.status, organizer.states.succeeded.value)

    def test_extend(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(1000, 'EUR'))
        PledgePaymentFactory.create(donation=donation)

        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()

        # Run scheduled task
        tenant = connection.tenant
        check_funding_end()
        with LocalTenant(tenant, clear_tenant=True):
            self.funding.refresh_from_db()

        self.assertEqual(self.funding.status, 'succeeded')

        self.funding.deadline = now() + timedelta(days=1)
        self.funding.save()

        # self.funding.states.extend()
        self.assertEqual(self.funding.status, 'open')

    def test_extend_past_deadline(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(1000, 'EUR'))
        PledgePaymentFactory.create(donation=donation)

        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()

        # Run scheduled task
        tenant = connection.tenant
        check_funding_end()
        with LocalTenant(tenant, clear_tenant=True):
            self.funding.refresh_from_db()

        self.assertEqual(self.funding.status, 'succeeded')

        self.assertRaises(
            TransitionNotPossible,
            self.funding.states.extend(save=True)
        )

    def test_refund(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(50, 'EUR'))
        PledgePaymentFactory.create(donation=donation)

        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()

        tenant = connection.tenant
        check_funding_end()

        with LocalTenant(tenant, clear_tenant=True):
            self.funding.refresh_from_db()

        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'partially_funded')
        self.funding.states.refund(save=True)

        for contribution in self.funding.donations.all():
            self.assertEqual(contribution.status, contribution.states.activity_refunded.value)

        self.funding.update_amounts()
        self.assertEqual(
            self.funding.amount_raised, donation.amount
        )

    def test_new_funding_for_running_initiative(self):
        new_funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(500, 'EUR'),
            deadline=now() + timedelta(weeks=2),
            bank_account=BankAccountFactory.create()
        )
        BudgetLineFactory.create(activity=new_funding)
        new_funding.bank_account.reviewed = True

        new_funding.states.reject(save=True)
        organizer = new_funding.contributions.first()
        self.assertEqual(organizer.status, u'failed')

        new_funding.states.restore(save=True)
        organizer.refresh_from_db()
        self.assertEqual(organizer.status, u'new')

        new_funding.states.approve(save=True)
        organizer.refresh_from_db()
        self.assertEqual(organizer.status, u'succeeded')
