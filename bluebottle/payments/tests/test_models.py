from collections import namedtuple
from django_fsm import TransitionNotAllowed
from mock import patch

from bluebottle import clients
from bluebottle.payments.services import PaymentService
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import (PaymentFactory,
                                                     OrderPaymentFactory)
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import StatusDefinition


class PaymentTestCase(BluebottleTestCase):
    def setUp(self):
        super(PaymentTestCase, self).setUp()
        self.init_projects()

        self.order = OrderFactory.create()
        self.order_payment = OrderPaymentFactory.create(order=self.order)

    def test_status_details(self):
        self.assertEqual(self.order_payment.status_description, "")
        self.assertEqual(self.order_payment.status_code, "")

    def test_basic_order_payment_flow(self):
        self.assertEqual(self.order.status, StatusDefinition.LOCKED,
                         'Creating an Order Payment should change Order to locked')

        self.assertEqual(self.order_payment.status, StatusDefinition.CREATED,
                         'Order Payment should start with created status')

        self.order_payment.started()
        self.order_payment.save()

        self.assertEqual(self.order.status, StatusDefinition.LOCKED,
                         'Starting an Order Payment should change Order to locked')
        self.assertEqual(self.order_payment.status, StatusDefinition.STARTED,
                         'Starting an Order Payment should change status to started')

        self.order_payment.authorized()
        self.order_payment.save()
        self.assertEqual(self.order.status, StatusDefinition.PENDING,
                         'Authorizing an Order Payment should change Order to pending')
        self.assertEqual(self.order_payment.status, StatusDefinition.AUTHORIZED,
                         'Authorizing an Order Payment should status to authorized')

        self.order_payment.settled()
        self.order_payment.save()
        self.assertEqual(self.order.status, StatusDefinition.SUCCESS,
                         'Settling an Order Payment should change Order to success')
        self.assertEqual(self.order_payment.status, StatusDefinition.SETTLED,
                         'Settling an Order Payment should change status to settled')

    def test_invalid_order_payment_flow(self):
        self.order_payment.started()
        self.order_payment.save()
        self.order_payment.authorized()
        self.order_payment.save()

        # Try to transition back to started
        with self.assertRaises(TransitionNotAllowed):
            self.order_payment.started()
            self.order_payment.save()

        # Try to transition to cancelled
        with self.assertRaises(TransitionNotAllowed):
            self.order_payment.cancelled()
            self.order_payment.save()

        self.assertEqual(self.order.status, StatusDefinition.PENDING,
                         'A failed Order Payment transition should not change Order status')

    def test_payment_status_changes(self):
        self.payment = PaymentFactory.create(order_payment=self.order_payment)

        self.assertEqual(self.order_payment.status, StatusDefinition.STARTED,
                         'Starting a Payment should change Order Payment to started')

        self.payment.status = StatusDefinition.AUTHORIZED
        self.payment.save()
        self.assertEqual(self.order_payment.status, StatusDefinition.AUTHORIZED,
                         'Authorizing a Payment should change Order Payment to authorized')
        self.assertEqual(self.order.status, StatusDefinition.PENDING,
                         'Authorizing a Payment should change Order Payment to pending')

    def test_bad_payment_status_changes(self):
        self.payment = PaymentFactory.create(order_payment=self.order_payment)
        self.payment.status = StatusDefinition.AUTHORIZED
        self.payment.save()

        self.assertEqual(self.order_payment.status, StatusDefinition.AUTHORIZED,
                         'Authorizing a Payment should change Order Payment to authorized')

        self.payment.status = StatusDefinition.STARTED

        # Starting an authorized Payment should not change Order Payment status
        with self.assertRaises(TransitionNotAllowed):
            self.payment.save()

        self.assertEqual(self.payment.order_payment.status,
                         StatusDefinition.AUTHORIZED,
                         'Starting an authorized Payment should not change Order Payment status')

        self.assertEqual(self.payment.order_payment.order.status,
                         StatusDefinition.PENDING,
                         'Starting an authorized Payment should not change Order status')

    def test_info_text(self):
        self.assertEqual(
            self.order_payment.info_text,
            'testserver via goodup {id}'.format(
                id=self.order_payment.id)
        )

    @patch.object(clients.utils, 'tenant_site')
    def test_info_text_onepercentclub(self, tenant_site_mock):
        tenant_site_mock.return_value = namedtuple(
            'Site', ['name', 'domain']
        )('1% club', 'onepercentclub.com')

        self.assertEqual(
            self.order_payment.info_text,
            'onepercentclub.com donation {id}'.format(id=self.order_payment.id)
        )

    def test_multiple_payments_to_an_order(self):
        """
        Test that a second order_payment can't transition an successful order.
        """

        second_order_payment = OrderPaymentFactory.create(order=self.order)

        self.order_payment.started()
        self.order_payment.authorized()
        self.order_payment.settled()
        self.order_payment.save()

        # Order should be successful now
        self.assertEqual(self.order.status, 'success')

        second_order_payment.started()
        second_order_payment.save()
        second_order_payment.failed()
        second_order_payment.save()

        # Order should still be successful
        self.assertEqual(self.order.status, 'success')


class OrderPaymentTestCase(BluebottleTestCase):
    def setUp(self):
        super(OrderPaymentTestCase, self).setUp()
        self.init_projects()

        self.order = OrderFactory.create()
        self.donation = DonationFactory(amount=60, order=self.order)
        self.order_payment = OrderPaymentFactory.create(order=self.order)

    def test_order_payment_amount(self):
        """
        Check that order payment amount is updated post-save when
        the order amount has changed.
        """
        self.donation.amount = 20
        self.donation.save()
        self.order.save()

        self.order_payment.save()
        self.assertEqual(self.order_payment.amount.amount, 20)


class PaymentFeeTestCase(BluebottleTestCase):
    def setUp(self):
        super(PaymentFeeTestCase, self).setUp()
        self.init_projects()

        self.order = OrderFactory.create()
        self.donation = DonationFactory(amount=60, order=self.order)
        self.order_payment = OrderPaymentFactory.create(order=self.order)

    def test_fixed_transaction_fee(self):
        """
        Check that the flat 0.75 mockIdeal fee is set
        """
        self.order_payment.payment_method = 'mockIdeal'
        self.order_payment.save()
        PaymentService(self.order_payment)
        self.assertEqual(self.order_payment.transaction_fee, 0.75)

    def test_relative_transaction_fee(self):
        """
        Check that the 3.25% mockCard fee is calculated
        """
        self.assertEqual(self.order.total.amount, 60)
        self.order_payment.payment_method = 'mockCard'
        self.order_payment.save()
        PaymentService(self.order_payment)
        self.assertEqual(self.order_payment.transaction_fee, 1.95)

    def test_changing_fee_when_changing_payment_method(self):
        """
        Check that the fee changes when we change payment method
        """
        self.order_payment.payment_method = 'mockIdeal'
        self.order_payment.save()
        PaymentService(self.order_payment)
        self.assertEqual(self.order_payment.transaction_fee, 0.75)
        self.order_payment.payment_method = 'mockCard'
        self.order_payment.save()
        self.assertEqual(self.order_payment.transaction_fee, 1.95)


class UtilsTestCase(BluebottleTestCase):
    def test_trim_url(self):
        from ..models import trim_tenant_url

        tenant_url = 'www.holycrapthisisareallyreallylongurl.com'
        max_length = 30

        new_url = trim_tenant_url(max_length, tenant_url)
        self.assertEqual(len(new_url), max_length)
        self.assertTrue('...' in new_url)
