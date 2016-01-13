import pytz
import datetime

from datetime import date, timedelta
from django.utils import timezone

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
from ..utils import get_accounting_statistics, get_dashboard_values


class AccountingStatisticsTests(BluebottleTestCase):
    fixtures = ('initial_data', 'project_data')

    def setUp(self):
        super(AccountingStatisticsTests, self).setUp()

        self.today = timezone.now()
        last_year = self.today.year - 1
        self.last_year = datetime.datetime(last_year, 1, 1, tzinfo=pytz.timezone('Europe/Amsterdam'))
        self.middle_date = datetime.datetime(last_year, 6, 1, tzinfo=pytz.timezone('Europe/Amsterdam'))

        # other categories from the fixtures are [u'Checking to savings', u'Savings to checking',
        # u'Bank costs', u'Donations to be transferred', u'Interest', u'Settle Bank costs', u'Total']
        self.CAMPAIGN_PAYOUT = BankTransactionCategory.objects.get(name='Campaign Payout')
        self.DOCDATA_PAYOUT = BankTransactionCategory.objects.get(name='Docdata payout')
        self.DOCDATA_PAYMENT = BankTransactionCategory.objects.get(name='Docdata payment')

        self.status = BankTransaction.IntegrityStatus # .Valid .UnknownTransaction .AmountMismatch
        self.creditdebit = BankTransaction.CreditDebit # .credit  .debit

        # ##### One organization has 2 projects ##### #
        self.organization = OrganizationFactory.create(name='test_org', slug='test_org')
        self.project1_owner = BlueBottleUserFactory(username='proj1_owner', email='owner@proj1.nl', password='proj1')
        self.project2_owner = BlueBottleUserFactory(username='proj2_owner', email='owner@proj2.nl', password='proj2')

        # deadline defaults to timezone.now() + timedelta(days=100)
        #  allow_overfunding defaults to True
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

        # ##### ORDER PAYMENT AND PAYMENT ##### #
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

        BankTransactionFactory.create(amount=Decimal('1000'),
                                      category=self.CAMPAIGN_PAYOUT,
                                      credit_debit=self.creditdebit.credit,
                                      status=self.status.Valid,
                                      payout=self.project2_payout,
                                      remote_payout=None,
                                      remote_payment=None,
                                      )

    def test_get_accounting_statistics(self):
        stats = get_accounting_statistics(self.last_year, self.today + timedelta(days=1))

        stats_keys = stats.keys()
        self.assertEqual(set(stats_keys), {'project_payouts', 'donations', 'docdata', 'bank', 'orders'})

        # ##### DONATIONS ##### #
        # only donations that have an order with status 'success' appear in the donations stats
        stats_donations = stats['donations']
        self.assertEqual(stats_donations.get('count'), 3) # 111 + 222 + 1000
        self.assertEqual(stats_donations.get('total_amount'), Decimal('1333'))

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
        self.assertEqual(stats_project_payouts.get('raised'), Decimal('1333')) # 1000 + 333
        self.assertEqual(stats_project_payouts.get('payable'),Decimal('1283')) # 1333 -50 (organization fee)
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
        # count is another item in the dict, so when checking a positive count, it does not
        # guarantee that the other item contains an existing queryset, so always check both
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
        self.assertEqual(project_payouts_count, 2)
        self.assertEqual(project_payouts_amount, Decimal('1333'))
        # PENDING
        project_payouts_pending = values.get('project_payouts_pending')
        project_payouts_pending_amount = values.get('project_payouts_pending_amount')
        self.assertFalse(project_payouts_pending.exists())
        self.assertEqual(project_payouts_pending_amount, Decimal())
        # PENDING NEW
        project_payouts_pending_new = values.get('project_payouts_pending_new')
        project_payouts_pending_new_count = values.get('project_payouts_pending_new_count')
        project_payouts_pending_new_amount = values.get('project_payouts_pending_new_amount')
        self.assertFalse(project_payouts_pending_new.exists())
        self.assertEqual(project_payouts_pending_new_count, 0)
        self.assertEqual(project_payouts_pending_new_amount, Decimal())
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
        self.assertFalse(invalid_order_payments.exists()) # empty queryset
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

    def test_statistics_more_complex_case(self):
        """
        Besides all orders, donations and transactions that are created in the SetUp,
        this test creates:

        - two more BankTransactions (one remotePayout and one remotePayment)
        - one extra donation that belongs to an failed order
        - one order payment that has no payment, its should appear in the invalid_order_payments
        - one transaction that has IntegretyStatus mismatch
        - one project_payouts with status = 'in_progress'
        - one project_payout with status = 'new'
        - one more bank transaction (not connected to any payout or payment) that is debit

        and all these cases are checked to appear correctly in the statistics ouput
        """
        # ##### EXTRA BANK TRANSACTIONS (RemotePayout and RemotePayment) ##### #
        remoteDDPayout1 = RemoteDocdataPayoutFactory.create(collected_amount=Decimal('1.11'),
                                                            payout_amount=Decimal('1.11'))
        BankTransactionFactory.create(amount=Decimal('1.11'), category=self.DOCDATA_PAYOUT,
                                      credit_debit=self.creditdebit.credit, status=self.status.Valid,
                                      payout=None,
                                      remote_payout=remoteDDPayout1,
                                      remote_payment=None)
        remoteDDPayout2 = RemoteDocdataPayoutFactory.create(collected_amount=Decimal('0.14'),
                                                                payout_amount=Decimal('0.14'))
        remoteDDPayment = RemoteDocdataPaymentFactory.create(remote_payout=remoteDDPayout2,
                                                             local_payment=self.payment,
                                                             amount_collected=Decimal('0.14'),
                                                             docdata_fee=Decimal('0.02'))
        BankTransactionFactory.create(amount=Decimal('0.14'), category=self.DOCDATA_PAYMENT,
                                      credit_debit=self.creditdebit.credit, status=self.status.Valid,
                                      payout=None,
                                      remote_payout=None,
                                      remote_payment=remoteDDPayment)

        # ##### EXTRA DONATION ##### #
        failed_order = OrderFactory.create(user=self.person2, status='failed')
        failed_donation = DonationFactory(order=failed_order, project=self.project1, amount=33000)

        # ##### EXTRA ORDER PAYMENT ##### #
        order = OrderFactory.create(user=self.person2)
        self.assertEqual(order.status, 'created')

        order_payment = OrderPaymentFactory.create(order=order, amount=Decimal('77'))
        self.assertEqual(OrderPayment.objects.filter(payment=None).first().pk, order_payment.pk)
        self.assertEqual(order_payment.amount, Decimal()) # because it has no payment

        # ##### EXTRA BANKTRANSACTIONS  ##### #
        BankTransactionFactory.create(amount=Decimal('77'),
                                      category=self.CAMPAIGN_PAYOUT,
                                      credit_debit=self.creditdebit.credit,
                                      status=self.status.UnknownTransaction,
                                      payout=None,
                                      remote_payout=None,
                                      remote_payment=None,
                                      )
        BankTransactionFactory.create(amount=Decimal('500'),
                                      category=self.CAMPAIGN_PAYOUT,
                                      credit_debit=self.creditdebit.debit,
                                      status=self.status.Valid,
                                      payout=None,
                                      remote_payout=None,
                                      remote_payment=None,
                                      )

        # ##### EXTRA PROJECT_PAYOUT ##### #
        ProjectPayoutFactory.create(
            completed=self.middle_date, status=StatusDefinition.IN_PROGRESS, project=self.project1,
            amount_raised=444, organization_fee=0, amount_payable=444)

        ProjectPayoutFactory.create(
            completed=self.middle_date, status=StatusDefinition.NEW, project=self.project1,
            amount_raised=Decimal('22.95'), organization_fee=0, amount_payable=Decimal('22.95'))

        #
        # #### TEST STATISTICS #### #
        #
        stats = get_accounting_statistics(self.last_year, self.today + timedelta(days=1))
        stats_keys = stats.keys()
        self.assertEqual(set(stats_keys), {'project_payouts', 'donations', 'docdata', 'bank', 'orders'})

        # ##### DONATIONS ##### #
        # only donations that have an order with status 'success' appear in the donations stats
        stats_donations = stats['donations']
        self.assertEqual(stats_donations.get('count'), 3) # 111 + 222 for project 1 and 1000 for project 2
        self.assertEqual(stats_donations.get('total_amount'), Decimal('1333'))

        # ##### ORDER PAYMENTS ##### #
        # only project 1 is added to an order payment
        stats_orders = stats['orders']
        self.assertEqual(stats_orders.get('count'), 1)
        self.assertEqual(stats_orders.get('total_amount'), Decimal('333.00'))
        self.assertEqual(stats_orders.get('transaction_fee'), Decimal())

        # ##### PROJECT PAYOUTS ##### #
        stats_project_payouts = stats['project_payouts']
        self.assertEqual(stats_project_payouts.get('count'), 4) # includes one in progress, and one pending
        self.assertEqual(stats_project_payouts.get('organization_fee'), Decimal('50'))
        self.assertEqual(stats_project_payouts.get('raised'), Decimal('1799.95')) # 1000 + 333 + 444 + 22.95
        self.assertEqual(stats_project_payouts.get('payable'),Decimal('1749.95')) # above - 50

        # ##### DOCDATA ##### #
        stats_docdata = stats['docdata']
        self.assertEqual(stats_docdata.get('pending_orders'), Decimal('311.75')) # = 333 - 20 - 1.11 - 0.14
        self.assertEqual(stats_docdata.get('pending_payout'), Decimal('122.48')) #  123.45 + 0.14 - 1.11
        self.assertEqual(stats_docdata.get('pending_service_fee'), Decimal('-0.35')) # 0.33 + 0.02

        stats_docdata_payment = stats_docdata['payment']
        self.assertEqual(stats_docdata_payment.get('count'), 2)
        self.assertEqual(stats_docdata_payment.get('docdata_fee'), Decimal('0.35')) # 0.33 + 0.02
        self.assertEqual(stats_docdata_payment.get('third_party'), Decimal())
        self.assertEqual(stats_docdata_payment.get('total_amount'), Decimal('123.59')) # 123.45 + 0.14

        stats_docdata_payout = stats_docdata['payout']
        self.assertEqual(stats_docdata_payout.get('count'), 3)
        self.assertEqual(stats_docdata_payout.get('other_costs'), Decimal('101.99')) # = 123.45 - (20 + 0.33) -(1.11 + 0.02)
        self.assertEqual(stats_docdata_payout.get('total_amount'),Decimal('21.25')) # 20 + 1.11 + 0.14

        # ##### BANK ##### #
        stats_bank = stats['bank']

        # ##### BANK ALL ##### #
        stats_bank_all = stats_bank[0]
        self.assertEqual(stats_bank_all.get('name'), 'All')
        self.assertEqual(stats_bank_all.get('account_number'), '')
        self.assertEqual(stats_bank_all.get('count'), 5)
        self.assertEqual(stats_bank_all.get('credit'), Decimal('1078.25')) # 1000 + 77 (mismatch) + 1.11 + 0.14
        self.assertEqual(stats_bank_all.get('debit'), Decimal('500'))
        self.assertEqual(stats_bank_all.get('balance'), Decimal('578.25'))

        per_category = stats_bank_all['per_category']
        for cat_dict in per_category:
            if cat_dict.get('category') == self.CAMPAIGN_PAYOUT:
                self.assertEqual(cat_dict.get('credit'), Decimal('1077')) # 1000 + 77 (mismatch)
                self.assertEqual(cat_dict.get('debit'), Decimal('500'))
                self.assertEqual(cat_dict.get('balance'), Decimal('577'))
            elif cat_dict.get('category') == self.DOCDATA_PAYOUT:
                self.assertEqual(cat_dict.get('credit'), Decimal('1.11'))
                self.assertEqual(cat_dict.get('debit'), Decimal())
                self.assertEqual(cat_dict.get('balance'), Decimal('1.11'))
            elif cat_dict.get('category') == self.DOCDATA_PAYMENT:
                self.assertEqual(cat_dict.get('credit'), Decimal('0.14'))
                self.assertEqual(cat_dict.get('debit'), Decimal())
                self.assertEqual(cat_dict.get('balance'), Decimal('0.14'))
            else: # all other categories should have zero
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

        #
        # ##### TEST DASHBOARD VALUES ##### #
        #
        values = get_dashboard_values(self.last_year, self.today + timedelta(days=1))

        # ##### DONATIONS ##### #
        donations = values.get('donations')
        donations_count = values.get('donations_count')
        donations_amount = values.get('donations_amount')
        self.assertTrue(donations.exists())
        self.assertEqual(donations_count, 4) # also includes failed order
        self.assertEqual(donations_amount, Decimal('34333')) # 33000 (failed order) + 1000 + 222 + 111

        donations_settled = values.get('donations_settled')
        donations_settled_count = values.get('donations_settled_count')
        donations_settled_amount = values.get('donations_settled_amount')
        self.assertTrue(donations_settled.exists())
        self.assertEqual(donations_settled_count, 3)
        self.assertEqual(donations_settled_amount, Decimal('1333'))

        donations_failed = values.get('donations_failed')
        donations_failed_count = values.get('donations_failed_count')
        donations_failed_amount = values.get('donations_failed_amount')
        self.assertTrue(donations_failed.exists())
        self.assertEqual(donations_failed_count, 1)
        self.assertEqual(donations_failed_amount, Decimal(33000))

        # ##### PROJECT PAYOUTS ##### #
        project_payouts = values.get('project_payouts')
        project_payouts_count = values.get('project_payouts_count')
        project_payouts_amount = values.get('project_payouts_amount')
        self.assertTrue(project_payouts.exists())
        self.assertEqual(project_payouts_count, 4) # includes in 'progress' and 'new' payout
        self.assertEqual(project_payouts_amount, Decimal('1799.95')) # 1000 + 333 + 444 + 22.95
        # PENDING
        project_payouts_pending = values.get('project_payouts_pending')
        project_payouts_pending_amount = values.get('project_payouts_pending_amount')
        self.assertTrue(project_payouts_pending.exists())
        self.assertEqual(project_payouts_pending_amount, Decimal('466.95')) # 444 + 22.95
        # PENDING NEW
        project_payouts_pending_new = values.get('project_payouts_pending_new')
        project_payouts_pending_new_count = values.get('project_payouts_pending_new_count')
        project_payouts_pending_new_amount = values.get('project_payouts_pending_new_amount')
        self.assertTrue(project_payouts_pending_new.exists())
        self.assertEqual(project_payouts_pending_new_count, 1)
        self.assertEqual(project_payouts_pending_new_amount, Decimal('22.95'))
        # PENDING IN PROGRESS
        project_payouts_pending_in_progress = values.get('project_payouts_pending_in_progress')
        project_payouts_pending_in_progress_amount = values.get('project_payouts_pending_in_progress_amount')
        project_payouts_pending_in_progress_count = values.get('project_payouts_pending_in_progress_count')
        self.assertTrue(project_payouts_pending_in_progress.exists())
        self.assertEqual(project_payouts_pending_in_progress_count, 1)
        self.assertEqual(project_payouts_pending_in_progress_amount, Decimal('444'))
        # PENDING SETTLED
        project_payouts_settled = values.get('project_payouts_settled')
        project_payouts_settled_count = values.get('project_payouts_settled_count')
        project_payouts_settled_amount = values.get('project_payouts_settled_amount')
        self.assertTrue(project_payouts_settled.exists())
        self.assertEqual(project_payouts_settled_count, 2)
        self.assertEqual(project_payouts_settled_amount, Decimal('1333')) # 1000 + 333

        # ##### ORDER PAYMENTS ##### #
        order_payments = values.get('order_payments')
        order_payments_count = values.get('order_payments_count')
        order_payments_amount = values.get('order_payments_amount')
        self.assertTrue(order_payments.exists())
        self.assertEqual(order_payments_count, 2) # the valid one and the failed one
        self.assertEqual(order_payments_amount, Decimal('333')) # 333 + 0 (failed one does not have value)

        invalid_order_payments = values.get('invalid_order_payments')
        invalid_order_payments_count = values.get('invalid_order_payments_count')
        invalid_order_payments_amount = values.get('invalid_order_payments_amount')
        invalid_order_payments_transaction_fee = values.get('invalid_order_payments_transaction_fee')
        self.assertTrue(invalid_order_payments.exists())
        self.assertEqual(invalid_order_payments_count, 1)
        self.assertEqual(invalid_order_payments_amount, Decimal()) # failed one has no value
        self.assertEqual(invalid_order_payments_transaction_fee, Decimal())

        # ##### DOCDATA PAYMENTS ##### #
        remote_docdata_payments = values.get('remote_docdata_payments')
        remote_docdata_payments_count = values.get('remote_docdata_payments_count')
        remote_docdata_payments_amount = values.get('remote_docdata_payments_amount')
        self.assertTrue(remote_docdata_payments.exists())
        self.assertEqual(remote_docdata_payments_count, 2)
        self.assertEqual(remote_docdata_payments_amount, Decimal('123.59')) # 123.45 + 0.14

        # ##### DOCDATA PAYOUTS ##### #
        remote_docdata_payouts = values.get('remote_docdata_payouts')
        remote_docdata_payouts_count = values.get('remote_docdata_payouts_count')
        remote_docdata_payouts_amount = values.get('remote_docdata_payouts_amount')
        self.assertTrue(remote_docdata_payouts.exists())
        self.assertEqual(remote_docdata_payouts_count, 3)
        self.assertEqual(remote_docdata_payouts_amount, Decimal('21.25')) # 20 + 0.14 + 1.11

        # ##### BANK TRANSACTIONS ##### #
        transactions = values.get('transactions')
        transactions_count = values.get('transactions_count')
        transactions_amount = values.get('transactions_amount')
        self.assertTrue(transactions.exists())
        self.assertEqual(transactions_count, 5) # 1000 + 1.11 + 0.14 + 77 (mismatch) + 500 (debit transaction)
        # NOTE: amount below is currently not used in the admin
        # when decided to use it, verify if it makes sense to add the debit and credit together
        # maybe credit - debit is expected, and the value should be 578.25 in that case
        self.assertEqual(transactions_amount, Decimal('1578.25'))

        invalid_transactions = values.get('invalid_transactions')
        invalid_transactions_count = values.get('invalid_transactions_count')
        invalid_transactions_amount = values.get('invalid_transactions_amount')
        self.assertTrue(invalid_transactions.exists())
        self.assertEqual(invalid_transactions_count, 1)
        self.assertEqual(invalid_transactions_amount, Decimal('77'))
