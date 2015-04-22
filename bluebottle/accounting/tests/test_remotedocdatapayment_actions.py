import hashlib
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from django_webtest import WebTestMixin

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounting import RemoteDocdataPaymentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectPhaseFactory
from bluebottle.bb_payouts.models import BaseProjectPayout
from bluebottle.payments_docdata.models import DocdataPayment
from bluebottle.payments_docdata.tests.factory_models import DocdataPaymentFactory


from bluebottle.utils.utils import StatusDefinition
from ..models import RemoteDocdataPayment


class RemoteDocdataPaymentActionTests(WebTestMixin, BluebottleTestCase):

    def setUp(self):
        super(RemoteDocdataPaymentActionTests, self).setUp()
        self.app.extra_environ['HTTP_HOST'] = self.tenant.domain_url
        self.superuser = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)

    def _initialize_payments(self):
        """
        Initialize some projects, donations, payments.
        """
        # required for project save
        ProjectPhaseFactory.create(name='Plan - submitted', slug='plan-submitted', sequence=2)

        self.project1 = ProjectFactory.create(status__name='Campaign', status__sequence=5)  # has no payout
        # has a new payout
        self.project2 = ProjectFactory.create(status__name='Done - Complete', status__sequence=9)
        # has an in_progress payout
        self.project3 = ProjectFactory.create(status__name='Done - Complete', status__sequence=9)
        # has a settled payout
        self.project4 = ProjectFactory.create(status__name='Done - Complete', status__sequence=9)

        # make donations for each project
        status_progressions = [
            # successful order
            (StatusDefinition.AUTHORIZED, StatusDefinition.SETTLED),
            # successful order, but RDP says it's chargeback
            (StatusDefinition.AUTHORIZED, StatusDefinition.SETTLED),
            # successful order, but RDP says it's refund
            (StatusDefinition.AUTHORIZED, StatusDefinition.SETTLED),
            # cancelled
            (StatusDefinition.CANCELLED,),
            # chargeback
            (StatusDefinition.AUTHORIZED, StatusDefinition.SETTLED, StatusDefinition.CHARGED_BACK),
            # refunded
            (StatusDefinition.AUTHORIZED, StatusDefinition.SETTLED, StatusDefinition.REFUNDED),
            # something else went wrong
            (StatusDefinition.AUTHORIZED, StatusDefinition.SETTLED, StatusDefinition.FAILED),
        ]
        for i, progressions in enumerate(status_progressions):

            order = OrderFactory.create()
            order_payment = OrderPaymentFactory.create(order=order)
            cluster_id = 'payment%d' % (i+1)

            DonationFactory.create(project=self.project1, order=order, amount=5)
            DonationFactory.create(project=self.project2, order=order, amount=10)
            DonationFactory.create(project=self.project3, order=order, amount=15)
            DonationFactory.create(project=self.project4, order=order, amount=20)

            payment = DocdataPaymentFactory.create(
                order_payment=order_payment,
                status=StatusDefinition.STARTED,
                merchant_order_id=cluster_id,
                payment_cluster_id=cluster_id,
                payment_cluster_key=hashlib.md5('%d' % order.pk).hexdigest(),
                default_pm='visa',
                total_gross_amount=order.total * 100,
            )

            # do the status progression, this sets of the order/order_payment status progression
            for status in progressions:
                payment.status = status
                payment.save()

        # some messed up situations
        j = len(status_progressions)
        _payments = []
        for i in range(j, j+2):
            order = OrderFactory.create()
            order_payment = OrderPaymentFactory.create(order=order)
            cluster_id = 'payment%d' % (i+1)

            DonationFactory.create(project=self.project1, order=order, amount=5)
            DonationFactory.create(project=self.project2, order=order, amount=10)

            payment = DocdataPaymentFactory.create(
                order_payment=order_payment,
                status=StatusDefinition.STARTED,
                merchant_order_id=cluster_id,
                payment_cluster_id=cluster_id,
                payment_cluster_key=hashlib.md5('%d' % order.pk).hexdigest(),
                default_pm='visa',
                total_gross_amount=order.total * 100,
            )
            _payments.append(payment)
            order_payment.authorized()
            order_payment.settled()

        DocdataPayment.objects.filter(id__in=[p.id for p in _payments]).update(status=StatusDefinition.SETTLED)

        # create remotedocdata payments that should match 7/9 of the local payments
        self.rdp_list = []
        for i, payment_type in enumerate(
                ('paid', 'chargedback', 'refund', None, 'chargedback', 'refund', None)
                ):
            if payment_type is None:
                continue
            amount_collected = Decimal(50) if payment_type == 'paid' else -Decimal(50)
            rdp = RemoteDocdataPaymentFactory.create(
                local_payment=None,
                triple_deal_reference='pid123456789t',
                payment_type=payment_type,
                merchant_reference='payment%d' % (i+1),
                amount_collected=amount_collected
            )
            self.rdp_list.append(rdp)
        for payment_type in ('chargedback', 'refund'):
            i = i + 1
            rdp = RemoteDocdataPaymentFactory.create(
                local_payment=None,
                triple_deal_reference='pid123456789t',
                payment_type=payment_type,
                merchant_reference='payment%d' % (i+1),
                amount_collected=-Decimal(15)
            )
            self.rdp_list.append(rdp)

        self.assertEqual(RemoteDocdataPayment.objects.count(), 7)

        # make some assertions
        for project in [self.project1, self.project2]:
            project.update_amounts(save=True)
            self.assertEqual(project.donation_set.count(), 9)  # = len(status_progressions) + 2 weirdo's

        for project in [self.project3, self.project4]:
            project.update_amounts(save=True)
            self.assertEqual(project.donation_set.count(), 7)  # = len(status_progressions)

        # bring payouts in desired state
        self.assertFalse(self.project1.projectpayout_set.exists())

        payout2 = self.project2.projectpayout_set.first()
        payout2.payout_rule = BaseProjectPayout.PayoutRules.not_fully_funded
        self.assertEqual(payout2.status, StatusDefinition.NEW)
        self.assertEqual(payout2.amount_raised, 50)

        payout3 = self.project3.projectpayout_set.first()
        payout3.payout_rule = BaseProjectPayout.PayoutRules.not_fully_funded
        payout3.in_progress()
        self.assertEqual(payout3.amount_raised, 45)

        payout4 = self.project4.projectpayout_set.first()
        payout4.payout_rule = BaseProjectPayout.PayoutRules.not_fully_funded
        payout4.in_progress()
        payout4.settled()
        self.assertEqual(payout4.amount_raised, 60)

    def _match_payments(self, n_payments):
        """
        Fetches the admin list view and tries to match all RDP's.
        """
        admin_url = reverse('admin:accounting_remotedocdatapayment_changelist')

        # verify that the transactions are visible
        payment_list = self.app.get(admin_url, user=self.superuser)
        self.assertEqual(payment_list.status_code, 200)
        # one for each transaction
        self.assertEqual(payment_list.pyquery('.action-checkbox').length, n_payments)

        # check the checkboxes and submit the action
        form = payment_list.forms['changelist-form']
        form['action'].select('find_matches')
        for i in range(0, n_payments):
            form.get('_selected_action', index=i).checked = True
        payment_list = form.submit().follow()
        return payment_list

    def test_refunds_chargebacks(self):
        """
        Test that all refunds/chargebacks are handled appropriately.

        Test the admin matching action.
        Test the 'mark donations failed' action.
        Test the 'take cut from organization fees' action.
        """

        self._initialize_payments()
        payment_list = self._match_payments(7)  # 7 remotedocdatapayments

        self.assertContains(payment_list, _('Payment object'), count=7)
        self.assertContains(payment_list, _('Invalid: inconsistent chargeback'), count=4)  # 3 are valid
        # 2 have project payouts
        self.assertContains(payment_list, _('take cut from organization fees'), count=2)
        # one without payout, one with a new payout that can be recalculated
        self.assertContains(payment_list, _('mark donations failed'), count=2)
        self.assertContains(payment_list, _('Valid'), count=4)  # 3 + 1 filter

        # now check that the actions work as expected

        # for payment2|3, chargedback|refund and has payouts
        for rdp in self.rdp_list[1:2]:
            self.assertTrue(rdp.has_problematic_payouts)
            url = reverse('admin:accounting_remotedocdatapayment_take_cut', args=[rdp.pk])
            confirmation = self.app.get(url, user=self.superuser)
            self.assertEqual(confirmation.status_code, 200)
