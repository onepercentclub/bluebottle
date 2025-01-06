import mock
from datetime import timedelta
from django.core import mail
from django.db import connection
from django.utils import timezone
from django.utils.timezone import now
from djmoney.money import Money

from bluebottle.clients.utils import LocalTenant
from bluebottle.funding.tasks import funding_tasks, donor_tasks
from bluebottle.funding.tests.factories import BudgetLineFactory, FundingFactory, DonorFactory
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.funding_stripe.tests.factories import ExternalAccountFactory, StripePayoutAccountFactory
from bluebottle.initiatives.tests.factories import (
    InitiativeFactory
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class FundingScheduledTasksTestCase(BluebottleTestCase):

    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            deadline=now() + timedelta(days=10),
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = StripePayoutAccountFactory.create(
            account_id="test-account-id", status="verified"
        )
        self.bank_account = ExternalAccountFactory.create(connect_account=payout_account, status='verified')
        self.funding.bank_account = self.bank_account
        self.funding.save()
        self.funding.states.submit()
        self.funding.states.approve(save=True)

    def test_funding_scheduled_task_expired(self):
        mail.outbox = []
        tenant = connection.tenant
        with mock.patch.object(timezone, 'now', return_value=(timezone.now() + timedelta(days=20))):
            funding_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'cancelled')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'Your crowdfunding campaign has expired'
        )

    def test_funding_scheduled_task_succeed(self):
        donation = DonorFactory.create(
            activity=self.funding,
            user=BlueBottleUserFactory.create(),
            amount=Money(1000, 'EUR')
        )
        PledgePaymentFactory.create(donation=donation)
        self.funding.deadline = now() - timedelta(days=1)
        mail.outbox = []
        tenant = connection.tenant
        with mock.patch.object(timezone, 'now', return_value=(timezone.now() + timedelta(days=20))):
            funding_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            self.funding.refresh_from_db()

        self.assertEqual(self.funding.status, 'succeeded')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'Your campaign "{}" has been successfully completed! \U0001f389'.format(self.funding.title)
        )

    def test_funding_scheduled_task_partial(self):
        donation = DonorFactory.create(
            activity=self.funding,
            user=BlueBottleUserFactory.create(),
            amount=Money(500, 'EUR')
        )
        PledgePaymentFactory.create(donation=donation)
        self.funding.deadline = now() - timedelta(days=1)
        mail.outbox = []
        tenant = connection.tenant
        with mock.patch.object(timezone, 'now', return_value=(timezone.now() + timedelta(days=20))):
            funding_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'partially_funded')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'Your crowdfunding campaign deadline passed'
        )


class DonorScheduledTasksTestCase(BluebottleTestCase):

    def setUp(self):
        self.donor = DonorFactory.create()

    def test_donor_not_yet_expired(self):
        with mock.patch.object(timezone, 'now', return_value=(timezone.now() + timedelta(days=10))):
            donor_tasks()

        self.donor.refresh_from_db()
        self.assertEqual(self.donor.status, 'new')

        self.assertEqual(len(self.donor.contributions.all()), 1)
        self.assertEqual(self.donor.contributions.all()[0].status, 'new')

    def test_donor_expired(self):
        with mock.patch.object(timezone, 'now', return_value=(timezone.now() + timedelta(days=20))):
            donor_tasks()

        self.donor.refresh_from_db()

        self.assertEqual(self.donor.status, 'expired')

        self.assertEqual(len(self.donor.contributions.all()), 1)
        self.assertEqual(self.donor.contributions.all()[0].status, 'failed')

    def test_donor_succeeded_not_expired(self):
        self.donor.states.succeed(save=True)

        with mock.patch.object(timezone, 'now', return_value=(timezone.now() + timedelta(days=20))):
            donor_tasks()

        self.donor.refresh_from_db()

        self.assertEqual(self.donor.status, 'succeeded')

        self.assertEqual(len(self.donor.contributions.all()), 1)
        self.assertEqual(self.donor.contributions.all()[0].status, 'succeeded')
