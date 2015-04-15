from datetime import date, timedelta
from django.test.utils import override_settings

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounting import (
    RemoteDocdataPayoutFactory, RemoteDocdataPaymentFactory, BankTransactionFactory)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.factory_models.payments import PaymentFactory, OrderPaymentFactory
from bluebottle.test.factory_models.payouts import ProjectPayoutFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.bb_payouts.models import *
from bluebottle.payments_docdata.models import *

from ..models import BankTransaction, RemoteDocdataPayment, RemoteDocdataPayout, BankTransactionCategory
from ..utils import get_accounting_statistics, get_dashboard_values, get_datefiltered_qs

# in settings.testing is DOCDATA_FEES
# but  @override_settings(DOCDATA_FEES={'transaction': 0.33,
#                                   'payment_methods': {'ideal': 0.33}})
# does not work

class AccountingStatisticsTests(BluebottleTestCase):
    fixtures = ('initial_data', 'project_data')


    def setUp(self):
        super(AccountingStatisticsTests, self).setUp()

        self.today = date.today()
        last_year = self.today.year - 1
        self.last_year = date(last_year, 1, 1)
        self.middle_date = date(last_year, 6, 1) # june 1st

        self.bankcategories = BankTransactionCategory.objects.all()

        self.status = BankTransaction.IntegrityStatus # .Valid .UnknownTransaction .AmountMismatch
        self.creditdebit = BankTransaction.CreditDebit # .credit  .debit

        # ##### One organization has 2 projects ##### #
        self.organization = OrganizationFactory.create(name='test_org', slug='test_org')
        self.project1_owner = BlueBottleUserFactory(username='proj1_owner', email='owner@proj1.nl', password='proj1')
        self.project2_owner = BlueBottleUserFactory(username='proj2_owner', email='owner@proj2.nl', password='proj2')

         # deadline defaults to timezone.now() + timedelta(days=100) # allow_overfunding defaults to  True
        self.project1 =  ProjectFactory(owner=self.project1_owner, organization=self.organization,
                                        title='Project 1', amount_needed=1111, amount_asked=1111)
        self.project2 = ProjectFactory(owner=self.project2_owner, organization=self.organization,
                                       title='Project 2', amount_needed=2222, amount_asked=2222)

        # ##### Person 1 makes 1 order that contains 2 donations for both projects ##### #
        self.person1 = BlueBottleUserFactory(username='Person One', email='pers@one.nl', password='secret')
        self.order1 = OrderFactory.create(user=self.person1)
        self.donation1_person1 = DonationFactory(order=self.order1, project=self.project1, amount=111)
        self.donation2_person1 = DonationFactory(order=self.order1, project=self.project2, amount=222)

        # ##### Person 2 makes 1 donations for project 1 ##### #
        self.person2 = BlueBottleUserFactory(username='Person Two', email='pers@two.nl', password='secret')
        self.order2 = OrderFactory.create(user=self.person2, status='success')
        self.donation1_person2 = DonationFactory(order=self.order2, project=self.project1, amount=1000)

        # #####
        self.assertEqual(self.order1.status, 'created')
        self.order_payment = OrderPaymentFactory.create(order=self.order1)
        self.assertEqual(self.order1.status, 'locked')
        self.assertEqual(Payment.objects.all().count(), 0)
        self.order_payment.started()
        self.payment = PaymentFactory.create(order_payment=self.order_payment)
        self.assertEqual(Payment.objects.all().count(), 1)
        self.assertEqual(self.order1.status, StatusDefinition.LOCKED)
        self.order_payment.authorized()
        self.assertEqual(self.order1.status, StatusDefinition.PENDING)
        self.order_payment.settled()
        self.assertEqual(self.order1.status, StatusDefinition.SUCCESS)
        # #####

        # ##### make Docdata Payout and Payment ##### #
        self.remoteDDPayout = RemoteDocdataPayoutFactory.create(collected_amount=Decimal('123.45'),
                                                                payout_amount=Decimal('20'))
        self.remoteDDPayment = RemoteDocdataPaymentFactory.create(remote_payout=self.remoteDDPayout,
                                                                  local_payment=self.payment,
                                                                  amount_collected=Decimal('123.45'),
                                                                  docdata_fee=Decimal('0.33'))
        self.assertEqual(self.remoteDDPayout.collected_amount, Decimal('123.45'))
        self.assertEqual(self.remoteDDPayout.payout_amount, Decimal('20'))
        self.assertEqual(self.remoteDDPayment.amount_collected, Decimal('123.45'))
        self.assertEqual(self.remoteDDPayment.docdata_fee, Decimal('0.33'))
        self.assertEqual(self.remoteDDPayment.status, 'valid')

        # completed should be between start and end to appear in the statistics
        self.project1_payout = ProjectPayoutFactory.create(
            completed=self.middle_date, status = StatusDefinition.SETTLED, project=self.project1,
            amount_raised=333, organization_fee=0, amount_payable=333)
        self.project2_payout = ProjectPayoutFactory.create(
            completed=self.middle_date, status = StatusDefinition.SETTLED, project=self.project2,
            amount_raised=1000, organization_fee=50, amount_payable=950)

        # create some banktransactions
        BankTransactionFactory.create(amount=Decimal('1000'),
                                      category=self.bankcategories.first(),
                                      credit_debit=self.creditdebit.credit,
                                      status=self.status.Valid,
                                      payout__project=self.project2,
                                      payout__organization_fee=50,
                                      payout__amount_raised=Decimal('1000'),
                                      payout__amount_payable=Decimal('50'), # completed, status, planned
                                      remote_payout=None, # RemoteDocdataPayoutFactory,
                                      remote_payment=None, # RemoteDocdataPaymentFactory,
                                      )

    def test_get_accounting_statistics(self):
        stats = get_accounting_statistics(self.last_year, self.today + timedelta(days=1))

        stats_keys = stats.keys()
        self.assertEqual(set(stats_keys), {'project_payouts', 'donations', 'docdata', 'bank', 'orders'})

        # ##### DONATIONS ##### #
        # only donations that have an order with status 'success' appear in the donations stats
        stats_donations = stats['donations']
        self.assertEqual(stats_donations.get('count'), 3)
        self.assertEqual(stats_donations.get('total_amount'), Decimal('1333'))  # 333 for project 1 and 1000 for project 2

        # ##### ORDER PAYMENTS ##### #
        # only project 1 is added to an order payment
        stats_orders = stats['orders']
        self.assertEqual(stats_orders.get('count'), 1)
        self.assertEqual(stats_orders.get('total_amount'), Decimal('333.00'))
        self.assertEqual(stats_orders.get('transaction_fee'), Decimal())

        # ##### PROJECT PAYOUTS ##### #
        stats_project_payouts = stats['project_payouts']
        self.assertEqual(stats_project_payouts.get('count'), 2)
        self.assertEqual(stats_project_payouts.get('organization_fee'), Decimal('50'))
        self.assertEqual(stats_project_payouts.get('payable'),Decimal('1283')) # 1333 -50
        self.assertEqual(stats_project_payouts.get('raised'), Decimal('1333'))
        # stats_project_payouts.get('per_payout_rule')

        # ##### DOCDATA ##### #
        stats_docdata = stats['docdata']
        self.assertEqual(stats_docdata.get('pending_orders'), Decimal('313')) # = 333 - 20
        self.assertEqual(stats_docdata.get('pending_payout'), Decimal('123.45'))
        self.assertEqual(stats_docdata.get('pending_service_fee'), Decimal('-0.33'))

        stats_docdata_payment = stats_docdata['payment']
        self.assertEqual(stats_docdata_payment.get('count'), 1)
        self.assertEqual(stats_docdata_payment.get('docdata_fee'), Decimal('0.33'))
        self.assertEqual(stats_docdata_payment.get('third_party'), Decimal())
        self.assertEqual(stats_docdata_payment.get('total_amount'), Decimal('123.45'))

        stats_docdata_payout = stats_docdata['payout']
        self.assertEqual(stats_docdata_payout.get('count'), 1)
        self.assertEqual(stats_docdata_payout.get('other_costs'), Decimal('103.12')) # = 123.45 - 0.33 - 20
        self.assertEqual(stats_docdata_payout.get('total_amount'),Decimal('20.00'))

        # ##### BANK ##### #
        stats_bank = stats['bank']

        # ##### BANK ALL ##### #
        stats_bank_all = stats_bank[0]
        self.assertEqual(stats_bank_all.get('name'), 'All')
        self.assertEqual(stats_bank_all.get('account_number'), '')
        self.assertEqual(stats_bank_all.get('balance'), Decimal('1000'))
        self.assertEqual(stats_bank_all.get('count'), 1)
        self.assertEqual(stats_bank_all.get('credit'), Decimal('1000'))
        self.assertEqual(stats_bank_all.get('debit'), 0)

        per_category = stats_bank_all['per_category']
        # only non 0 values expected for 'Campaign payout'
        for cat_dict in per_category:
            if cat_dict.get('category') == BankTransactionCategory.objects.get(name='Campaign Payout'):
                self.assertEqual(cat_dict.get('credit'), 1000)
                self.assertEqual(cat_dict.get('debit'), 0)
                self.assertEqual(cat_dict.get('balance'), 1000)
            else:
                self.assertEqual(cat_dict.get('credit'), 0)
                self.assertEqual(cat_dict.get('debit'), 0)
                self.assertEqual(cat_dict.get('balance'), 0)

        # ##### BANK CHECKINGS##### #
        stats_bank_checking = stats_bank[1]
        self.assertEqual(stats_bank_checking.get('name'), 'Checking account')
        self.assertEqual(stats_bank_checking.get('balance'), Decimal())
        self.assertEqual(stats_bank_checking.get('count'), 0)
        self.assertEqual(stats_bank_checking.get('credit'), Decimal())
        self.assertEqual(stats_bank_checking.get('debit'), 0)

        # ##### BANK SAVINGS##### #
        stats_bank_savings = stats_bank[2]
        self.assertEqual(stats_bank_savings.get('name'), 'Savings account')
        self.assertEqual(stats_bank_savings.get('balance'), Decimal())
        self.assertEqual(stats_bank_savings.get('count'), 0)
        self.assertEqual(stats_bank_savings.get('credit'), Decimal())
        self.assertEqual(stats_bank_savings.get('debit'), 0)

    def test_get_dashboard_values(self):
        values = get_dashboard_values(self.last_year, self.today + timedelta(days=1))

        values_keys = values.keys()
        expected_keys = ['project_payouts_pending_new_count',
                         'remote_docdata_payments',
                         'invalid_transactions',
                         'remote_docdata_payments_amount',
                         'donations_settled_amount',
                         'remote_docdata_payouts',
                         'donations_settled',
                         'project_payouts_pending_new_amount',
                         'remote_docdata_payments_count',
                         'transactions_amount',
                         'order_payments_count',
                         'invalid_order_payments_transaction_fee',
                         'donations_failed_amount',
                         'donations',
                         'project_payouts_settled',
                         'donations_amount',
                         'project_payouts_pending_in_progress_count',
                         'invalid_order_payments',
                         'project_payouts_settled_amount',
                         'project_payouts_pending_amount',
                         'transactions',
                         'project_payouts_amount',
                         'transactions_count',
                         'remote_docdata_payouts_amount',
                         'project_payouts_settled_count',
                         'donations_failed_count',
                         'project_payouts_count',
                         'project_payouts_pending',
                         'project_payouts_pending_new',
                         'order_payments',
                         'invalid_transactions_amount',
                         'project_payouts_pending_in_progress',
                         'order_payments_amount',
                         'project_payouts',
                         'invalid_order_payments_amount',
                         'donations_failed',
                         'project_payouts_pending_in_progress_amount',
                         'donations_count',
                         'donations_settled_count',
                         'invalid_transactions_count',
                         'invalid_order_payments_count',
                         'remote_docdata_payouts_count']
        self.assertEqual(set(values_keys), set(expected_keys))

        # ##### DONATIONS ##### #
        donations = values.get('donations')
        donations_count = values.get('donations_count')
        donations_amount = values.get('donations_amount')
        self.assertTrue(donations.exists())
        self.assertEqual(donations_count, 3)
        self.assertEqual(donations_amount, Decimal('1333'))

        donations_settled = values.get('donations_settled')
        donations_settled_count = values.get('donations_settled_count')
        donations_settled_amount = values.get('donations_settled_amount')
        self.assertTrue(donations_settled.exists())
        self.assertEqual(donations_settled_count, 3)
        self.assertEqual(donations_settled_amount, Decimal('1333'))

        donations_failed = values.get('donations_failed')
        donations_failed_count = values.get('donations_failed_count')
        donations_failed_amount = values.get('donations_failed_amount')
        self.assertFalse(donations_failed.exists()) # empty queryset
        self.assertEqual(donations_failed_count, 0)
        self.assertEqual(donations_failed_amount, Decimal())

        # ##### PROJECT PAYOUTS ##### #
        project_payouts = values.get('project_payouts')
        project_payouts_count = values.get('project_payouts_count')
        project_payouts_amount = values.get('project_payouts_amount')
        self.assertTrue(project_payouts.exists())
        self.assertEqual(project_payouts_count, 3)
        self.assertEqual(project_payouts_amount, Decimal('2333'))
        # PENDING
        project_payouts_pending = values.get('project_payouts_pending')
        project_payouts_pending_amount = values.get('project_payouts_pending_amount')
        self.assertTrue(project_payouts_pending.exists())
        self.assertEqual(project_payouts_pending_amount, Decimal('1000'))
        # PENDING NEW
        project_payouts_pending_new = values.get('project_payouts_pending_new')
        project_payouts_pending_new_count = values.get('project_payouts_pending_new_count')
        project_payouts_pending_new_amount = values.get('project_payouts_pending_new_amount')
        self.assertTrue(project_payouts_pending_new.exists())
        self.assertEqual(project_payouts_pending_new_count, 1)
        self.assertEqual(project_payouts_pending_new_amount, Decimal('1000'))
        # PENDING IN PROGRESS
        project_payouts_pending_in_progress = values.get('project_payouts_pending_in_progress')
        project_payouts_pending_in_progress_amount = values.get('project_payouts_pending_in_progress_amount')
        project_payouts_pending_in_progress_count = values.get('project_payouts_pending_in_progress_count')
        self.assertFalse(project_payouts_pending_in_progress.exists())
        self.assertEqual(project_payouts_pending_in_progress_count, 0)
        self.assertEqual(project_payouts_pending_in_progress_amount, Decimal())
        # PENDING SETTLED
        project_payouts_settled = values.get('project_payouts_settled')
        project_payouts_settled_count = values.get('project_payouts_settled_count')
        project_payouts_settled_amount = values.get('project_payouts_settled_amount')
        self.assertTrue(project_payouts_settled.exists())
        self.assertEqual(project_payouts_settled_count, 2)
        self.assertEqual(project_payouts_settled_amount, Decimal('1333'))

        # ##### ORDER PAYMENTS ##### #
        order_payments = values.get('order_payments')
        order_payments_count = values.get('order_payments_count')
        order_payments_amount = values.get('order_payments_amount')
        self.assertTrue(order_payments.exists())
        self.assertEqual(order_payments_count, 1)
        self.assertEqual(order_payments_amount, Decimal('333'))

        invalid_order_payments = values.get('invalid_order_payments')
        invalid_order_payments_count = values.get('invalid_order_payments_count')
        invalid_order_payments_amount = values.get('invalid_order_payments_amount')
        invalid_order_payments_transaction_fee = values.get('invalid_order_payments_transaction_fee')
        self.assertFalse(invalid_order_payments.exists())  # empty queryset
        self.assertEqual(invalid_order_payments_count, 0)
        self.assertEqual(invalid_order_payments_amount, Decimal())
        self.assertEqual(invalid_order_payments_transaction_fee, Decimal())

        # ##### DOCDATA PAYMENTS ##### #
        remote_docdata_payments = values.get('remote_docdata_payments')
        remote_docdata_payments_count = values.get('remote_docdata_payments_count')
        remote_docdata_payments_amount = values.get('remote_docdata_payments_amount')
        self.assertTrue(remote_docdata_payments.exists())
        self.assertEqual(remote_docdata_payments_count, 1)
        self.assertEqual(remote_docdata_payments_amount, Decimal('123.45'))

        # ##### DOCDATA PAYOUTS ##### #
        remote_docdata_payouts = values.get('remote_docdata_payouts')
        remote_docdata_payouts_count = values.get('remote_docdata_payouts_count')
        remote_docdata_payouts_amount = values.get('remote_docdata_payouts_amount')
        self.assertTrue(remote_docdata_payouts.exists())
        self.assertEqual(remote_docdata_payouts_count, 1)
        self.assertEqual(remote_docdata_payouts_amount, Decimal('20'))

        # ##### BANK TRANSACTIONS ##### #
        transactions = values.get('transactions')
        transactions_count = values.get('transactions_count')
        transactions_amount = values.get('transactions_amount')
        self.assertTrue(transactions.exists())
        self.assertEqual(transactions_count, 1)
        self.assertEqual(transactions_amount, Decimal('1000'))

        invalid_transactions = values.get('invalid_transactions')
        invalid_transactions_count = values.get('invalid_transactions_count')
        invalid_transactions_amount = values.get('invalid_transactions_amount')
        self.assertFalse(invalid_transactions.exists()) # empty QuerySet
        self.assertEqual(invalid_transactions_count, 0)
        self.assertEqual(invalid_transactions_amount, Decimal())
