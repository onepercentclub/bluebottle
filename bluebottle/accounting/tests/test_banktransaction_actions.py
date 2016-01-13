from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.translation import ugettext as _

from django_webtest import WebTestMixin
from bluebottle.bb_projects.models import ProjectPhase

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.accounting import BankTransactionFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectPhaseFactory
from bluebottle.bb_payouts.models import BaseProjectPayout
from bluebottle.utils.model_dispatcher import get_organization_payout_model
from bluebottle.utils.utils import StatusDefinition
from bluebottle.payments_manual.models import ManualPayment
from ..models import BankTransaction


@override_settings(MINIMAL_PAYOUT_AMOUNT=-1)
class BankTransactionActionTests(WebTestMixin, BluebottleTestCase):

    def setUp(self):
        super(BankTransactionActionTests, self).setUp()
        self.init_projects()
        self.app.extra_environ['HTTP_HOST'] = self.tenant.domain_url
        self.superuser = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)

    def _add_completed_donation(self, project, amount):
        donation = DonationFactory.create(project=project, amount=amount)
        donation.order.locked()
        donation.order.succeeded()

    def _initialize_unmatched_transactions(self):
        # required for project save
        start = timezone.now() - timedelta(days=10)
        status_campaign = ProjectPhase.objects.get(slug='campaign')
        status_done = ProjectPhase.objects.get(slug='done-complete')

        # projects to match with
        self.project1 = ProjectFactory.create(status=status_campaign)
        self.project2 = ProjectFactory.create(status=status_campaign,
                                              amount_asked=200)
        self.project3 = ProjectFactory.create(status=status_campaign,
                                              amount_asked=200)
        self.project4 = ProjectFactory.create(status=status_campaign,
                                              amount_asked=200)

        # Close some of the projects
        self.project2.status = status_done
        self.project2.save()
        self.project3.status = status_done
        self.project3.save()
        self.project4.status = status_done
        self.project4.save()

        # update payout for project 2 & 3, no donations exist yet so just make it zero/empty
        # adding a new donation (for a closed payout) should create a new payout
        payout2 = self.project2.projectpayout_set.first()
        payout2.payout_rule = BaseProjectPayout.PayoutRules.not_fully_funded
        payout2.in_progress()
        payout2.settled()

        payout3 = self.project3.projectpayout_set.first()
        payout3.payout_rule = BaseProjectPayout.PayoutRules.not_fully_funded
        payout3.in_progress()
        payout3.settled()

        # should be updated with new donation
        payout4 = self.project4.projectpayout_set.first()
        payout4.payout_rule = BaseProjectPayout.PayoutRules.not_fully_funded
        payout4.save()
        self.assertEqual(payout4.status, StatusDefinition.NEW)

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

        # create an organization payout
        now = date.today()
        OrganizationPayout = get_organization_payout_model()
        self.org_payout = OrganizationPayout(
            start_date=now - timedelta(days=7),
            end_date=now + timedelta(days=7),
            planned=now + timedelta(days=8)
        )
        self.org_payout.save()

    def _match_banktransactions(self, expected_action, n_transactions):
        """
        Fetches the list and executes the list action to match the bank transactions.

        :param expected_action: string as expected to be visible.
        """
        admin_url = reverse('admin:accounting_banktransaction_changelist')

        # verify that the transactions are visible
        transaction_list = self.app.get(admin_url, user=self.superuser)
        self.assertEqual(transaction_list.status_code, 200)
        # one for each transaction
        self.assertEqual(transaction_list.pyquery('.action-checkbox').length, n_transactions)

        # 'try' to match them and check that they have the appropriate statuses and actions in the admin

        # check the checkboxes and submit the action
        form = transaction_list.forms['changelist-form']
        form['action'].select('find_matches')
        for i in range(0, len(self.transactions)):
            form.get('_selected_action', index=i).checked = True
        transaction_list = form.submit().follow()

        # all transactions must be marked as 'unknown'
        transactions = BankTransaction.objects.filter(status=BankTransaction.IntegrityStatus.UnknownTransaction)
        self.assertEqual(transactions.count(), n_transactions)

        # verify that the action 'create donation' is visible
        self.assertContains(transaction_list, expected_action, count=4)

    def test_manual_donation(self):
        """
        Test that an unmatched bank transaction can be resolved by creating a
        donation.

        Creating a donation means that an order with ManualPayment has to be
        created. The full amount (=no fees) goes to the project. The donated
        amount must enter the payout flow so the project receives the donation.
        """
        admin_url = reverse('admin:accounting_banktransaction_changelist')
        self._initialize_unmatched_transactions()
        self._match_banktransactions(_('create donation'), 4)

        # pick the action 'create donation' for each transaction
        for i, transaction in enumerate(self.transactions):
            project = getattr(self, 'project%d' % (i+1))
            url = reverse('admin:banktransaction-add-manualdonation', kwargs={'pk': transaction.pk})
            donation_form = self.app.get(url, user=self.superuser)
            self.assertEqual(donation_form.status_code, 200)
            form = donation_form.forms[1]

            # fill in the form and submit
            form['project'] = project.pk
            response = form.submit()
            self.assertRedirects(response, admin_url)
            self.assertEqual(response.follow().status_code, 200)

            # verify that an extra donation is created
            self.assertEqual(project.donation_set.count(), 1)
            donation = project.donation_set.last()
            self.assertTrue(donation.anonymous)
            self.assertEqual(donation.amount, Decimal(75))
            self.assertEqual(donation.user, self.superuser)
            self.assertEqual(donation.project, project)

            # verify that an order exists
            self.assertIsNotNone(donation.order)
            order = donation.order
            self.assertEqual(order.order_payments.count(), 1)
            order_payment = order.order_payments.first()
            self.assertEqual(order.status, StatusDefinition.SUCCESS)
            self.assertEqual(order_payment.status, StatusDefinition.SETTLED)
            self.assertEqual(order_payment.amount, Decimal(75))
            self.assertEqual(order.user, self.superuser)
            self.assertEqual(order_payment.user, self.superuser)
            self.assertEqual(order_payment.transaction_fee, Decimal(0))

            # verify that a payment exists and isisinstance of ManualPayment (Polymorphic Payment)
            payment = order_payment.payment
            self.assertIsInstance(payment, ManualPayment)
            self.assertEqual(payment.user, self.superuser)
            self.assertEqual(payment.amount, Decimal(75))
            self.assertEqual(payment.status, StatusDefinition.SETTLED)
            self.assertEqual(payment.transaction, transaction)

            # assert that the transaction is now valid
            transaction = BankTransaction.objects.get(pk=transaction.pk)
            self.assertEqual(transaction.status, BankTransaction.IntegrityStatus.Valid)

        # verify that the projectpayout is correctly dealt with
        payouts1 = self.project1.projectpayout_set.count()
        self.assertEqual(payouts1, 0)
        project1 = self.project1.__class__.objects.get(pk=self.project1.pk)
        self.assertEqual(project1.amount_donated, Decimal(75))

        payouts2 = self.project2.projectpayout_set.all()
        self.assertEqual(payouts2.count(), 2)  # a new one must be created
        # check that the sum and status are correct
        new_payout = payouts2.first()  # order by created
        new_payout.in_progress()
        new_payout.settled()
        self.assertTrue(new_payout.protected)
        self.assertEqual(new_payout.amount_raised, Decimal(75))
        project2 = self.project2.__class__.objects.get(pk=self.project2.pk)
        self.assertEqual(project2.amount_donated, Decimal(75))
        self.assertEqual(new_payout.amount_raised, Decimal(75))
        self.assertEqual(new_payout.amount_payable, Decimal('71.25'))
        self.assertEqual(new_payout.organization_fee, Decimal('3.75'))

        # similar to case 2
        payouts3 = self.project3.projectpayout_set.all()
        self.assertEqual(payouts3.count(), 2)  # a new one must be created
        # check that the sum and status are correct
        new_payout = payouts3.first()  # order by created
        new_payout.in_progress()
        new_payout.settled()
        self.assertTrue(new_payout.protected)
        self.assertEqual(new_payout.amount_raised, Decimal(75))
        project3 = self.project3.__class__.objects.get(pk=self.project3.pk)
        self.assertEqual(project3.amount_donated, Decimal(75))
        self.assertEqual(new_payout.amount_raised, Decimal(75))
        self.assertEqual(new_payout.amount_payable, Decimal('71.25'))
        self.assertEqual(new_payout.organization_fee, Decimal('3.75'))

        # payout 4 is new and should just be updated
        payouts4 = self.project4.projectpayout_set.all()
        self.assertEqual(payouts4.count(), 1)
        payout = payouts4.first()
        payout.in_progress()
        payout.settled()
        self.assertTrue(payout.protected)
        self.assertEqual(payout.amount_raised, Decimal(75))
        self.assertEqual(payout.amount_payable, Decimal('71.25'))
        self.assertEqual(payout.organization_fee, Decimal('3.75'))

        # make sure that the project signal is not broken
        self.assertTrue(project3.is_realised)
        self.assertTrue(project3.amount_asked)
        project3.save()  # triggers bb_payouts.signals.create_payout_finished_project

        # verify that organization payouts update correctly
        self.org_payout.calculate_amounts()
        self.assertEqual(self.org_payout.payable_amount_excl, Decimal('9.30'))
        # advance a manual donation payout to settled
        payout = payouts3.first()
        payout.in_progress()
        payout.settled()
        self.org_payout.calculate_amounts()
        self.assertEqual(self.org_payout.payable_amount_incl, Decimal('15.00'))

    def test_multiple_manual_donations(self):
        """
        Test that multiple manual donations correctly update a protected ProjectPayout
        """
        admin_url = reverse('admin:accounting_banktransaction_changelist')
        self._initialize_unmatched_transactions()
        self._match_banktransactions(_('create donation'), 4)

        # pick the action 'create donation' for each transaction
        project = self.project2  # project with settled payout -> creates a new payout
        for i, transaction in enumerate(self.transactions):
            url = reverse('admin:banktransaction-add-manualdonation', kwargs={'pk': transaction.pk})
            donation_form = self.app.get(url, user=self.superuser)
            self.assertEqual(donation_form.status_code, 200)
            form = donation_form.forms[1]

            # fill in the form and submit
            form['project'] = project.pk
            response = form.submit()
            self.assertRedirects(response, admin_url)
            self.assertEqual(response.follow().status_code, 200)

            # verify that the donation is created
            self.assertEqual(project.donation_set.count(), i+1)
            donation = project.donation_set.all()[i]
            self.assertTrue(donation.anonymous)
            self.assertEqual(donation.amount, Decimal(75))
            self.assertEqual(donation.user, self.superuser)
            self.assertEqual(donation.project, project)

            # verify that an order exists
            self.assertIsNotNone(donation.order)
            order = donation.order
            self.assertEqual(order.order_payments.count(), 1)
            order_payment = order.order_payments.first()
            self.assertEqual(order.status, StatusDefinition.SUCCESS)
            self.assertEqual(order_payment.status, StatusDefinition.SETTLED)
            self.assertEqual(order_payment.amount, Decimal(75))
            self.assertEqual(order.user, self.superuser)
            self.assertEqual(order_payment.user, self.superuser)
            self.assertEqual(order_payment.transaction_fee, Decimal(0))

            # verify that a payment exists and isisinstance of ManualPayment (Polymorphic Payment)
            payment = order_payment.payment
            self.assertIsInstance(payment, ManualPayment)
            self.assertEqual(payment.user, self.superuser)
            self.assertEqual(payment.amount, Decimal(75))
            self.assertEqual(payment.status, StatusDefinition.SETTLED)
            self.assertEqual(payment.transaction.id, transaction.id)

            # assert that the transaction is now valid
            transaction = BankTransaction.objects.get(pk=transaction.pk)
            self.assertEqual(transaction.status, BankTransaction.IntegrityStatus.Valid)

        payouts = project.projectpayout_set.all()
        self.assertEqual(payouts.count(), 2)
        aggregated = payouts.aggregate(Sum('amount_raised'), Sum('amount_payable'), Sum('organization_fee'))
        self.assertEqual(aggregated['amount_raised__sum'], 4*Decimal('75'))
        self.assertEqual(aggregated['amount_payable__sum'], 4*Decimal('71.25'))
        self.assertEqual(aggregated['organization_fee__sum'], 4*Decimal('3.75'))

    # def test_payout_retry(self):
    #     """
    #     Test the scenario where a payout bounces and the payout is retried.
    #
    #     The admin action is to match it with an existing payout. The existing
    #     payout needs updating - the status has to be set to 'retry' and must
    #     be available for export again. The amount_payable can be lowered with
    #     bank costs that have to be entered manually (transaction costs).
    #     """
    #     # initialize some data
    #     self._initialize_unmatched_transactions()
    #     project = self.project2
    #     transaction = self.transactions[0]  # for convenience, they're all the same
    #
    #     # create one donation, this payout will bounce
    #     donation = DonationFactory.create(project=project, amount=80)
    #     donation.order.locked()
    #     donation.order.pending()
    #     donation.order.save()
    #
    #     payouts = project.projectpayout_set.all()
    #     self.assertEqual(payouts.count(), 2)
    #     payout = payouts.first()
    #     payout.amount_raised = 80
    #     payout.organization_fee = 4
    #     payout.amount_payable = 76
    #     payout.planned = date.today() - timedelta(days=3)
    #     payout.save()
    #
    #     original_date = payout.planned
    #     original_completed = payout.completed
    #
    #     # assert that the 'retry payout' action is visible
    #     self._match_banktransactions(_('retry payout'), 4)
    #
    #     # enter the retry payout form
    #     admin_url = reverse('admin:banktransaction-retry-payout', kwargs={'pk': transaction.pk})
    #     retry_form = self.app.get(admin_url, user=self.superuser)
    #     self.assertEqual(retry_form.status_code, 200)
    #
    #     form = retry_form.forms[1]
    #     form['payout'] = payout.pk
    #     form['amount'] = 5
    #     response = form.submit()
    #
    #     # redirect_url = reverse('admin:payouts_projectpayout_change', args=[payout.pk])
    #     # self.assertRedirects(response, redirect_url)
    #
    #     # assert that the payout is protected
    #     payout = payout.__class__.objects.get(pk=payout.pk)
    #     payout.retry()
    #     self.assertTrue(payout.protected)
    #     self.assertTrue(payout.status, StatusDefinition.RETRY)
    #
    #     # assert that the amount_payable is lowered with the bank costs (-5 euro)
    #     self.assertEqual(payout.amount_raised, 80)
    #     self.assertEqual(payout.amount_payable, 71)
    #     self.assertEqual(payout.organization_fee, 4)
    #
    #     # assert that the payout has a valid next date
    #     self.assertNotEqual(payout.planned, original_date)
    #     self.assertGreaterEqual(payout.planned, date.today())
    #
    #     # the completed date needs to be the same, else it's collected again in organization payout
    #     self.assertEqual(payout.completed, original_completed)
    #
    #     # assert that the bank transaction is resolved/valid
    #     transaction = BankTransaction.objects.get(pk=transaction.pk)
    #     self.assertEqual(transaction.status, BankTransaction.IntegrityStatus.Valid)
    #     self.assertEqual(transaction.payout, payout)
