# -*- coding: utf-8 -*-
from datetime import timedelta, datetime

import mock
from django.core import mail
from django.db import connection
from django.utils import timezone
from django.utils.timezone import now, get_current_timezone
from moneyed import Money

from bluebottle.activities.models import Organizer
from bluebottle.clients.utils import LocalTenant
from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.funding.tasks import funding_tasks
from bluebottle.funding.tests.factories import FundingFactory, DonorFactory, \
    BudgetLineFactory, BankAccountFactory, PlainPayoutAccountFactory
from bluebottle.funding.tests.test_admin import generate_mock_bank_account
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.funding_stripe.tests.factories import StripePayoutAccountFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class FundingTestCase(BluebottleAdminTestCase):
    def setUp(self):
        super(FundingTestCase, self).setUp()
        user = BlueBottleUserFactory.create(first_name='Jean Baptiste')
        self.initiative = InitiativeFactory.create(activity_manager=user)
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        bank_account = generate_mock_bank_account()
        self.funding = FundingFactory.create(
            owner=user,
            initiative=self.initiative,
            target=Money(500, 'EUR'),
            deadline=now() + timedelta(weeks=2),
            bank_account=bank_account
        )
        BudgetLineFactory.create(activity=self.funding)
        self.funding.bank_account.reviewed = True

        self.funding.states.submit()
        self.funding.states.approve(save=True)
        BudgetLineFactory.create_batch(4, activity=self.funding, amount=Money(125, 'EUR'))
        mail.outbox = []

    def test_default_status(self):
        self.assertEqual(self.funding.status, self.funding.states.open.value)
        organizer = self.funding.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, organizer.states.succeeded.value)
        self.assertEqual(organizer.user, self.funding.owner)

    def test_review(self):
        funding = FundingFactory.create(initiative=self.initiative)
        self.assertEqual(funding.status, funding.states.draft.value)

        BudgetLineFactory.create(activity=funding)
        payout_account = PlainPayoutAccountFactory.create(status="verified")
        bank_account = BankAccountFactory.create(
            connect_account=payout_account, status="verified"
        )
        funding.bank_account = bank_account

        funding.states.submit(save=True)
        self.assertEqual(funding.status, funding.states.submitted.value)
        organizer = funding.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, organizer.states.new.value)
        self.assertEqual(organizer.user, funding.owner)

    def test_approve_deadline(self):
        funding = FundingFactory.create(
            owner=self.initiative.activity_manager,
            initiative=self.initiative,
            target=Money(500, 'EUR'),
            duration=30,
            deadline=None,
            bank_account=BankAccountFactory.create(
                status="verified",
                connect_account=StripePayoutAccountFactory.create(
                    account_id="test-account-id", status="verified"
                ),
            ),
        )

        self.assertIsNone(funding.started)

        BudgetLineFactory.create(activity=funding)

        funding.states.submit()
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

        # Run scheduled task
        tenant = connection.tenant
        future = now() + timedelta(weeks=12)
        with mock.patch.object(timezone, 'now', return_value=future):
            funding_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            self.funding.refresh_from_db()

        self.assertEqual(self.funding.status, 'cancelled')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your crowdfunding campaign has expired')
        self.assertTrue(self.funding.title in mail.outbox[0].body)
        self.assertTrue('Hi Jean Baptiste,' in mail.outbox[0].body)

    def test_some_donations(self):
        user = BlueBottleUserFactory.create(first_name='Bill')
        donation = DonorFactory.create(
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

        # Donor amount should appear in both emails
        self.assertTrue(u'50.00 €' in mail.outbox[0].body)
        self.assertTrue(u'50.00 €' in mail.outbox[1].body)

        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()

        # Run scheduled task
        tenant = connection.tenant
        funding_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            self.funding.refresh_from_db()

        self.assertEqual(self.funding.status, 'partially_funded')
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(mail.outbox[2].subject, 'Your crowdfunding campaign deadline passed')
        self.assertTrue('Hi Jean Baptiste,' in mail.outbox[0].body)
        self.assertTrue(self.funding.title in mail.outbox[0].body)
        url = 'http://testserver/en/activities/details/funding/{}/{}'.format(
            self.funding.id, self.funding.slug
        )
        self.assertTrue(url in mail.outbox[0].body)

    def test_enough_donations(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(300, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        donation = DonorFactory.create(activity=self.funding, amount=Money(450, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(len(mail.outbox), 4)
        self.assertEqual(donation.status, 'succeeded')
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()

        # Run scheduled task
        tenant = connection.tenant
        funding_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            self.funding.refresh_from_db()

        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            mail.outbox[4].subject,
            u'Your campaign "{}" has been successfully completed! \U0001f389'.format(
                self.funding.title
            )
        )
        self.assertTrue('Hi Jean Baptiste,' in mail.outbox[4].body)
        self.assertTrue(self.funding.title in mail.outbox[4].body)
        url = 'http://testserver/en/activities/details/funding/{}/{}'.format(
            self.funding.id, self.funding.slug
        )
        self.assertTrue(url in mail.outbox[4].body)

        organizer = self.funding.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, organizer.states.succeeded.value)

    def test_extend(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(1000, 'EUR'))
        PledgePaymentFactory.create(donation=donation)

        self.funding.deadline = now() + timedelta(days=1)
        self.funding.save()

        # Run scheduled task
        tenant = connection.tenant
        future = now() + timedelta(days=2)
        with mock.patch.object(timezone, 'now', return_value=future):
            funding_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            self.funding.refresh_from_db()

        self.assertEqual(self.funding.status, 'succeeded')

        self.funding.deadline = now() + timedelta(days=1)
        self.funding.save()

        # self.funding.states.extend()
        self.assertEqual(self.funding.status, 'open')

    def test_extend_past_deadline(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(1000, 'EUR'))
        PledgePaymentFactory.create(donation=donation)

        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()

        # Run scheduled task
        tenant = connection.tenant
        funding_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            self.funding.refresh_from_db()

        self.assertEqual(self.funding.status, 'succeeded')

        with self.assertRaises(TransitionNotPossible):
            self.funding.states.extend(save=True)

    def test_refund(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(50, 'EUR'))
        PledgePaymentFactory.create(donation=donation)

        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()

        tenant = connection.tenant
        funding_tasks()

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
            bank_account=BankAccountFactory.create(
                status="verified",
                connect_account=StripePayoutAccountFactory.create(
                    account_id="test-account-id", status="verified"
                ),
            ),
        )
        BudgetLineFactory.create(activity=new_funding)
        new_funding.bank_account.reviewed = True

        new_funding.states.reject(save=True)
        organizer = new_funding.contributors.first()
        self.assertEqual(organizer.status, u'failed')

        new_funding.states.restore(save=True)
        organizer.refresh_from_db()
        self.assertEqual(organizer.status, u'new')

        new_funding.states.submit()
        new_funding.states.approve(save=True)
        organizer.refresh_from_db()
        self.assertEqual(organizer.status, u'succeeded')
