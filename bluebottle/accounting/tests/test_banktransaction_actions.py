from datetime import date, timedelta
from decimal import Decimal

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from django_webtest import WebTestMixin

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.accounting import BankTransactionFactory
from bluebottle.test.factory_models.payouts import ProjectPayoutFactory
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectPhaseFactory
from bluebottle.utils.utils import StatusDefinition
from ..models import BankTransaction


class BankTransactionActionTests(WebTestMixin, BluebottleTestCase):

    def setUp(self):
        super(BankTransactionActionTests, self).setUp()
        self.app.extra_environ['HTTP_HOST'] = self.tenant.domain_url
        self.superuser = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)

    def _initialize_unmatched_transactions(self):
        # required for project save
        ProjectPhaseFactory.create(name='Plan - submitted', slug='plan-submitted', sequence=2)

        # projects to match with
        self.project1 = ProjectFactory.create(status__name='Campaign', status__sequence=5)
        self.project2 = ProjectFactory.create(status__name='Done - Complete', status__sequence=9)
        self.project3 = ProjectFactory.create(status__name='Done - Complete', status__sequence=9)
        self.project4 = ProjectFactory.create(status__name='Done - Complete', status__sequence=9)

        # create payout for project 2 & 3, no donations exist yet so just make it zero/empty
        # adding a new donation (for a closed payout) should create a new payout
        ProjectPayoutFactory.create(
            project=self.project2,
            amount_raised=0,
            organization_fee=0,
            amount_payable=0,
            status=StatusDefinition.SETTLED
        )

        # should be left alone
        ProjectPayoutFactory.create(
            project=self.project3,
            amount_raised=0,
            organization_fee=0,
            amount_payable=0,
            status=StatusDefinition.PENDING
        )

        # should be updated with new donation
        ProjectPayoutFactory.create(
            project=self.project4,
            amount_raised=0,
            organization_fee=0,
            amount_payable=0,
            status=StatusDefinition.NEW
        )

        # create a bank transaction to resolve. It's unmatched with anything.
        self.transactions = BankTransactionFactory.create_batch(
            4,
            payout=None,
            remote_payout=None,
            remote_payment=None,
            credit_debit='C',
            amount=Decimal(75),  # must create a donation of 75 euro
            book_date=date.today() - timedelta(days=3),
            description1='Unmatched donation'
        )

    def test_manual_donation(self):
        """
        Test that an unmatched bank transaction can be resolved by creating a
        donation.

        Creating a donation means that an order with ManualPayment has to be
        created. The full amount (=no fees) goes to the project. The donated
        amount must enter the payout flow so the project receives the donation.
        """
        self._initialize_unmatched_transactions()

        admin_url = reverse('admin:accounting_banktransaction_changelist')

        # verify that the transactions are visible
        transaction_list = self.app.get(admin_url, user=self.superuser)
        self.assertEqual(transaction_list.status_code, 200)
        # one for each transaction
        self.assertEqual(transaction_list.pyquery('.action-checkbox').length, 4)

        # 'try' to match them and check that they have the appropriate statuses and actions in the admin

        # check the checkboxes and submit the action
        form = transaction_list.forms['changelist-form']
        form['action'].select('find_matches')
        for i in range(0, len(self.transactions)):
            form.get('_selected_action', index=i).checked = True
        transaction_list = form.submit().follow()

        # all transactions must be marked as 'unknown'
        transactions = BankTransaction.objects.filter(status=BankTransaction.IntegrityStatus.UnknownTransaction)
        self.assertEqual(transactions.count(), 4)

        # verify that the action 'create donation' is visible
        self.assertContains(transaction_list, _('create donation'), count=4)

        # pick the action 'create donation' for each transaction

        # verify that a donation is created
        # verify that an order exists
        # verify that a exists and isisinstance of ManualPayment (Polymorphic Payment)
        # verify that the projectpayout is correctly dealt with
