from django.test import Client
from django.core.urlresolvers import reverse

from mock import patch

from bluebottle.payments.models import OrderPayment, Transaction
from bluebottle.payments.services import PaymentService
from bluebottle.payments_docdata.adapters import DocdataPaymentAdapter
from bluebottle.payments_docdata.tests.factory_models import (
    DocdataDirectdebitPaymentFactory, DocdataPaymentFactory,
    DocdataTransactionFactory)
from bluebottle.payments_logger.models import PaymentLogEntry
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase, FsmTestMixin
from bluebottle.utils.utils import StatusDefinition


# Mock create_payment so we don't need to call the external docdata service
def fake_create_payment(self):
    payment = self.MODEL_CLASS(order_payment=self.order_payment,
                               **self.order_payment.integration_data)
    payment.total_gross_amount = self.order_payment.amount
    payment.payment_cluster_key = 'abc123'
    payment.payment_cluster_id = 'abc123'
    payment.save()

    return payment


class PaymentsDocdataTestCase(BluebottleTestCase, FsmTestMixin):
    @patch('bluebottle.payments_docdata.adapters.gateway.DocdataClient')
    def setUp(self, mock_client):
        super(PaymentsDocdataTestCase, self).setUp()

        # Mock response to creating the payment at docdata
        instance = mock_client.return_value
        instance.create.return_value = {'order_key': 123, 'order_id': 123}

        # Mock create payment
        patch.object(DocdataPaymentAdapter, 'create_payment', fake_create_payment)
        self.order = OrderFactory.create()
        self.order_payment = OrderPaymentFactory.create(order=self.order,
                                                        payment_method='docdataIdeal',
                                                        integration_data={
                                                            'default_pm': 'ideal'})
        self.service = PaymentService(order_payment=self.order_payment)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_authorized_status(self, mock_fetch_status, mock_transaction):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED',
            totals={'totalAcquirerApproved': '1000', 'totalRegistered': '1000'}
        )

        self.service.check_payment_status()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment,
                           StatusDefinition.AUTHORIZED)
        self.assert_status(self.order_payment, StatusDefinition.AUTHORIZED)
        self.assert_status(self.order, StatusDefinition.PENDING)

        mock_transaction.assert_called_once_with(
            mock_fetch_status.return_value.payment[0])

    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_transaction(self, mock_fetch_status):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED',
            totals={'totalAcquirerApproved': '1000', 'totalRegistered': '1000'}
        )

        self.service.check_payment_status()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment,
                           StatusDefinition.AUTHORIZED)
        self.assert_status(self.order_payment, StatusDefinition.AUTHORIZED)
        self.assert_status(self.order, StatusDefinition.PENDING)

        transaction = Transaction.objects.get()
        self.assertEqual(transaction.authorization_amount, 1000)
        self.assertEqual(transaction.raw_response,
                         str(mock_fetch_status.return_value.payment[0]))

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_new(self, mock_fetch_status, mock_transaction):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response('NEW')

        self.service.check_payment_status()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment, StatusDefinition.STARTED)
        self.assert_status(self.order_payment, StatusDefinition.STARTED)
        self.assert_status(self.order, StatusDefinition.LOCKED)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_redirected(self, mock_fetch_status, mock_transaction):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'REDIRECTED_FOR_AUTHORIZATION')

        self.service.check_payment_status()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment, StatusDefinition.STARTED)
        self.assert_status(self.order_payment, StatusDefinition.STARTED)
        self.assert_status(self.order, StatusDefinition.LOCKED)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_authenticated(self, mock_fetch_status, mock_transaction):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHENTICATED')

        self.service.check_payment_status()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment, StatusDefinition.STARTED)
        self.assert_status(self.order_payment, StatusDefinition.STARTED)
        self.assert_status(self.order, StatusDefinition.LOCKED)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_error(self, mock_fetch_status, mock_transaction):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZATION_FAILED')

        self.service.check_payment_status()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment, StatusDefinition.FAILED)
        self.assert_status(self.order_payment, StatusDefinition.FAILED)
        self.assert_status(self.order, StatusDefinition.FAILED)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_settled(self, mock_fetch_status, mock_transaction):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED',
            totals={'totalCaptured': '1000', 'totalRegistered': '1000'}
        )

        self.service.check_payment_status()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment, StatusDefinition.SETTLED)
        self.assert_status(self.order_payment, StatusDefinition.SETTLED)
        self.assert_status(self.order, StatusDefinition.SUCCESS)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_chargeback(self, mock_fetch_status, mock_transaction):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED',
            totals={'totalCaptured': '1000', 'totalRegistered': '1000'}
        )

        self.service.check_payment_status()

        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED',
            totals={'totalCaptured': '1000', 'totalRegistered': '1000',
                    'totalChargedback': '1000'}
        )

        self.service.check_payment_status()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment,
                           StatusDefinition.CHARGED_BACK)
        self.assert_status(self.order_payment, StatusDefinition.CHARGED_BACK)
        self.assert_status(self.order, StatusDefinition.FAILED)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_refund(self, mock_fetch_status, mock_transaction):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED',
            totals={'totalCaptured': '1000', 'totalRegistered': '1000'}
        )

        self.service.check_payment_status()

        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED',
            totals={'totalCaptured': '1000', 'totalRegistered': '1000',
                    'totalRefunded': '1000'}
        )

        self.service.check_payment_status()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment,
                           StatusDefinition.REFUNDED)
        self.assert_status(self.order_payment, StatusDefinition.REFUNDED)
        self.assert_status(self.order, StatusDefinition.REFUNDED)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_chargeback_refund(self, mock_fetch_status, mock_transaction):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED',
            totals={'totalCaptured': '1000', 'totalRegistered': '1000'}
        )

        self.service.check_payment_status()

        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED',
            totals={'totalCaptured': '1000', 'totalRegistered': '1000',
                    'totalRefunded': '500', 'totalChargedback': '500'}
        )

        self.service.check_payment_status()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment,
                           StatusDefinition.REFUNDED)
        self.assert_status(self.order_payment, StatusDefinition.REFUNDED)
        self.assert_status(self.order, StatusDefinition.REFUNDED)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_two_payments(self, mock_fetch_status, mock_transaction):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED',
            payments=[{
                'id': '1234',
                'status': 'FAILED',
                'amount': '1000',
                'paymentMethod': 'MASTERCARD'
            }, {
                'id': '12345',
                'status': 'AUTHORIZED',
                'amount': '1000',
                'paymentMethod': 'MASTERCARD'
            }],
            totals={'totalCaptured': '1000', 'totalRegistered': '1000'}
        )

        self.service.check_payment_status()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment, StatusDefinition.SETTLED)
        self.assert_status(self.order_payment, StatusDefinition.SETTLED)
        self.assert_status(self.order, StatusDefinition.SUCCESS)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_partially_settled(self, mock_fetch_status, mock_transaction):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED',
            totals={'totalCaptured': '1000', 'totalRegistered': '1000'}
        )

        self.service.check_payment_status()

        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED',
            totals={'totalCaptured': '500', 'totalRegistered': '1000'}
        )

        self.service.check_payment_status()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment, StatusDefinition.UNKNOWN)
        self.assert_status(self.order_payment, StatusDefinition.UNKNOWN)
        self.assert_status(self.order, StatusDefinition.FAILED)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_failed_success_status(self, mock_fetch_status,
                                         mock_transaction):
        # Check the order can go from failed to success when the payment goes from
        # cancelled to paid.

        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response('CANCELED')

        self.service.check_payment_status()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment,
                           StatusDefinition.CANCELLED)
        self.assert_status(self.order_payment, StatusDefinition.CANCELLED)
        self.assert_status(self.order, StatusDefinition.FAILED)

        # Check that the status propagated through to order
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED',
            totals={'totalCaptured': '1000', 'totalRegistered': '1000'}
        )
        self.service.check_payment_status()

        self.assert_status(self.order_payment, StatusDefinition.SETTLED)
        self.assert_status(self.order, StatusDefinition.SUCCESS)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_no_payment_method_change(self, mock_fetch_status,
                                      mock_transaction):
        self.assertEquals(PaymentLogEntry.objects.count(), 1)

        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED')

        order = OrderFactory.create()
        order_payment = OrderPaymentFactory.create(
            order=order, payment_method='docdataCreditcard')
        docdata_payment = DocdataPaymentFactory.create(
            order_payment=order_payment,
            default_pm='mastercard',
            payment_cluster_id='1234',
            total_gross_amount=100)
        DocdataTransactionFactory.create(payment=docdata_payment,
                                         payment_method='VISA')
        c = Client()
        merchant_order_id = "{0}-1".format(order_payment.id)
        resp = c.get(reverse('docdata-payment-status-update',
                             kwargs={'merchant_order_id': merchant_order_id}))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, 'success')

        # Reload the order payment
        order_payment = OrderPayment.objects.get(id=order_payment.id)
        self.assertEqual(order_payment.payment_method, 'docdataCreditcard')

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_payment_method_change(self, mock_fetch_status, mock_transaction):
        self.skipTest('Skipping test until we update it.')
        # Two payment log entries already exist: 2x 'a new payment status "started" '
        self.assertEquals(PaymentLogEntry.objects.count(), 2)

        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED')

        order = OrderFactory.create()
        # Ensure that we use an existing payment_method or the adapter throws an exception
        order_payment = OrderPaymentFactory.create(
            order=order, payment_method='docdataPaypal')
        docdata_payment = DocdataPaymentFactory.create(
            order_payment=order_payment,
            default_pm='paypal',
            payment_cluster_id='1235',
            total_gross_amount=100)

        DocdataTransactionFactory.create(payment=docdata_payment,
                                         payment_method='VISA')
        c = Client()
        merchant_order_id = "{0}-1".format(order_payment.id)
        resp = c.get(reverse('docdata-payment-status-update',
                             kwargs={'merchant_order_id': merchant_order_id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, 'success')

        # # Reload the order payment
        order_payment = OrderPayment.objects.get(id=order_payment.id)
        self.assertEqual(order_payment.payment_method, 'docdataPaypal')

        # Check that all is logged correctly
        self.assertEquals(
            PaymentLogEntry.objects.filter(payment=docdata_payment).count(),
            5)  # The status changes triggers the
        # creation of more payment log entries
        log = PaymentLogEntry.objects.all()[0]
        self.assertEqual(log.message,
                         "{0} - Payment method changed for payment with id {1}"
                         " and order payment with id {2}.".format(
                             docdata_payment, docdata_payment.id,
                             docdata_payment.order_payment.id))
        self.assertEqual(log.payment.id, docdata_payment.id)
        self.assertEqual(log.level, 'INFO')

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_unknown_payment_method_change(self, mock_fetch_status,
                                           mock_transaction):
        self.skipTest('Skipping test until we update it.')

        # Two payment log entries already exist: 2x 'a new payment status "started" '
        self.assertEquals(PaymentLogEntry.objects.count(), 2)

        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED')

        order = OrderFactory.create()
        # Ensure that we use an existing payment_method or the adapter throws an exception
        order_payment = OrderPaymentFactory.create(order=order,
                                                   payment_method='docdataPaypal')
        docdata_payment = DocdataPaymentFactory.create(
            order_payment=order_payment,
            default_pm='paypal',
            payment_cluster_id='1236',
            total_gross_amount=100)

        DocdataTransactionFactory.create(payment=docdata_payment,
                                         payment_method='BLABLABLA')
        c = Client()
        merchant_order_id = "{0}-1".format(order_payment.id)
        resp = c.get(reverse('docdata-payment-status-update',
                             kwargs={'merchant_order_id': merchant_order_id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, 'success')

        # Reload the order payment
        order_payment = OrderPayment.objects.get(id=order_payment.id)
        self.assertEqual(order_payment.payment_method, 'docdataPaypal')

        # Check that all is logged correctly
        self.assertEquals(
            PaymentLogEntry.objects.filter(payment=docdata_payment).count(), 5)
        log = PaymentLogEntry.objects.all()[0]
        self.assertEqual(log.message,
                         "{0} - Payment method '{1}' not found for payment "
                         "with id {2} and order payment with id {3}.".format(
                             docdata_payment,
                             'BLABLABLA',
                             docdata_payment.id,
                             docdata_payment.order_payment.id))
        self.assertEqual(log.payment.id, docdata_payment.id)
        self.assertEqual(log.level, 'WARNING')


class AdapterTestCase(BluebottleTestCase):
    @patch('bluebottle.payments_docdata.adapters.gateway.DocdataClient')
    def test_incomplete_userdata(self, mock_client):
        # Mock response to creating the payment at docdata
        instance = mock_client.return_value
        instance.create.return_value = {'order_key': 123, 'order_id': 123}

        patch.object(DocdataPaymentAdapter, 'create_payment',
                     fake_create_payment)

        user = BlueBottleUserFactory()
        self.order = OrderFactory.create(user=user)
        self.order_payment = OrderPaymentFactory.create(
            order=self.order, payment_method='docdataIdeal',
            integration_data={'default_pm': 'ideal'})

        self.service = PaymentService(order_payment=self.order_payment)

        user_data = self.service.adapter.get_user_data()
        self.assertEqual(user_data['id'], user.id)
        self.assertEqual(user_data['first_name'], user.first_name)
        self.assertEqual(user_data['last_name'], user.last_name)
        self.assertEqual(user_data['email'], user.email)

        self.assertEqual(user_data['street'], 'Unknown')
        self.assertEqual(user_data['house_number'], 'Unknown')
        self.assertEqual(user_data['postal_code'], 'Unknown')
        self.assertEqual(user_data['city'], 'Unknown')
        self.assertEqual(user_data['country'], 'NL')

        self.assertEqual(user_data['company'], '')
        self.assertEqual(user_data['kvk_number'], '')
        self.assertEqual(user_data['vat_number'], '')
        self.assertEqual(user_data['house_number_addition'], '')
        self.assertEqual(user_data['state'], '')

    @patch('bluebottle.payments_docdata.adapters.gateway.DocdataClient')
    def test_normal_userdata(self, mock_client):
        # Mock response to creating the payment at docdata
        instance = mock_client.return_value
        instance.create.return_value = {'order_key': 123, 'order_id': 123}

        patch.object(DocdataPaymentAdapter, 'create_payment',
                     fake_create_payment)

        user = BlueBottleUserFactory()
        holland = CountryFactory(name='Netherlands', alpha2_code='NL')

        # Update user address
        user.address.line1 = 'Dam 1a'
        user.address.line2 = 'Bovenste bel'
        user.address.city = 'Amsterdam'
        user.address.postal_code = '1000AA'
        user.address.country = holland
        user.address.save()

        self.order = OrderFactory.create(user=user)
        self.order_payment = OrderPaymentFactory.create(order=self.order,
                                                        payment_method='docdataIdeal',
                                                        integration_data={
                                                            'default_pm': 'ideal'})

        self.service = PaymentService(order_payment=self.order_payment)

        user_data = self.service.adapter.get_user_data()
        self.assertEqual(user_data['id'], user.id)
        self.assertEqual(user_data['first_name'], user.first_name)
        self.assertEqual(user_data['last_name'], user.last_name)
        self.assertEqual(user_data['email'], user.email)

        self.assertEqual(user_data['street'], 'Dam')
        self.assertEqual(user_data['house_number'], '1a')
        self.assertEqual(user_data['postal_code'], '1000AA')
        self.assertEqual(user_data['city'], 'Amsterdam')
        self.assertEqual(user_data['country'], 'NL')

        self.assertEqual(user_data['company'], '')
        self.assertEqual(user_data['kvk_number'], '')
        self.assertEqual(user_data['vat_number'], '')
        self.assertEqual(user_data['house_number_addition'], '')
        self.assertEqual(user_data['state'], '')

    @patch('bluebottle.payments_docdata.adapters.gateway.DocdataClient')
    def test_abnormal_address_data(self, mock_client):
        # Mock response to creating the payment at docdata
        instance = mock_client.return_value
        instance.create.return_value = {'order_key': 123, 'order_id': 123}

        patch.object(DocdataPaymentAdapter, 'create_payment',
                     fake_create_payment)

        user = BlueBottleUserFactory()
        CountryFactory(name='Netherlands', alpha2_code='NL')

        # Update user address with abnormal line1
        user.address.line1 = '1a'
        user.address.save()

        self.order = OrderFactory.create(user=user)
        self.order_payment = OrderPaymentFactory.create(
            order=self.order, payment_method='docdataIdeal',
            integration_data={'default_pm': 'ideal'})

        self.service = PaymentService(order_payment=self.order_payment)

        user_data = self.service.adapter.get_user_data()
        self.assertEqual(user_data['street'], 'Unknown')


from django.test.utils import override_settings
from django.conf import settings
from bluebottle.payments.exception import PaymentException
from ..models import DocdataPayment


class DocdataModelTestCase(BluebottleTestCase):
    @override_settings(
        DOCDATA_FEES={})  # You must specify the overriden key, even if it will be removed
    def test_get_fee_no_docdata_fees(self):
        """ Test raised exception when DOCDATA_FEES is not present """
        del settings.DOCDATA_FEES

        payment = DocdataPayment()

        # For some reason, assertRaises wasn't catching this exception, even
        # though it was throwing it during the test. Therefore I used this
        # try/except block. (This is still OK according to
        # the Django docs)

        try:
            payment.get_fee()
            self.fail("No PaymentException raised")
        except PaymentException as e:
            self.assertEqual(e.message, "Missing fee DOCDATA_FEES")

    @override_settings(DOCDATA_FEES={})
    def test_get_fee_no_transaction(self):
        """
        Test that a Payment exception is raised when there is
        no 'transaction' key
        """

        payment = DocdataPayment()

        try:
            payment.get_fee()
            self.fail("No PaymentException raised")
        except PaymentException as e:
            self.assertEqual(e.message, "Missing fee 'transaction'")

    @override_settings(DOCDATA_FEES={'transaction': 0.20})
    def test_get_fee_no_payment_methods(self):
        """
        Test that a Payment exception is raised when there is no
        'payment_methods' key
        """

        payment = DocdataPayment()

        try:
            payment.get_fee()
            self.fail("No PaymentException raised")
        except PaymentException as e:
            self.assertEqual(e.message, "Missing fee 'payment_methods'")

    @override_settings(DOCDATA_FEES={'transaction': 0.20,
                                     'payment_methods': {'ideal': 0.35}})
    def test_get_fee_no_payment_method(self):
        """
        Test that a missing specific payment method raises a payment exception
        """
        pm = 'testpm'

        payment = DocdataPayment(default_pm=pm)

        try:
            payment.get_fee()
            self.fail("No PaymentException raised")
        except PaymentException as e:
            self.assertEqual(e.message, "Missing fee {0}".format(pm))

    @override_settings(DOCDATA_FEES={'transaction': 0.20,
                                     'payment_methods': {'ideal': 0.35}})
    def test_get_fee_absolute(self):
        """
        Test that a payment method with absolute fees returns the transaction
        amount and the payment method fee amount, e.g., the 'transaction'
        amount plus the 'ideal' amount.
        """
        pm = 'ideal'

        payment = DocdataPayment(default_pm=pm)

        fee_total = payment.get_fee()
        self.assertEqual(0.20 + 0.35, fee_total)

    @override_settings(DOCDATA_FEES={'transaction': 0.20,
                                     'payment_methods': {'ideal': '1.5%'}})
    def test_get_fee_relative(self):
        """
        Test that the correct fee is returned given the defined percentage.
        In this test case the amount is 100 and the fee percentage is 1.5%,
        so the result should be 100 * 0.015.
        """

        order_payment = OrderPaymentFactory.create(amount=1000)
        docdata_payment = DocdataPaymentFactory.create(
            order_payment=order_payment,
            default_pm='ideal',
            total_gross_amount=1000)
        order_payment.amount = 100
        fee_total = docdata_payment.get_fee()
        self.assertEqual(fee_total, 100 * 0.015)

    def test_direct_debit_wrong_pm(self):
        """
        Test that a direct debit payments default_pm will be forced
        to 'sepa_direct_debit'.
        """
        order_payment = OrderPaymentFactory.create(amount=1000)
        docdata_payment = DocdataDirectdebitPaymentFactory.create(
            order_payment=order_payment,
            default_pm='ideal',
            total_gross_amount=1000
        )
        self.assertEqual(docdata_payment.default_pm, 'sepa_direct_debit')
