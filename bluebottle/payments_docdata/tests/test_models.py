from datetime import datetime

from django.test import TestCase
from django_fsm.db.fields import TransitionNotAllowed
from django.test import Client
from django.core.urlresolvers import reverse

from bluebottle.test.factory_models.payments import PaymentFactory, OrderPaymentFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.models import TestBaseUser
from bluebottle.test.utils import FsmTestMixin

from bluebottle.payments.services import PaymentService
from bluebottle.payments_docdata.gateway import DocdataClient
from bluebottle.payments_docdata.adapters import DocdataPaymentAdapter

from bluebottle.utils.utils import StatusDefinition
from bluebottle.payments_docdata.tests.factory_models import DocdataPaymentFactory, DocdataTransactionFactory
from bluebottle.payments.models import OrderPayment 
from bluebottle.payments_logger.models import PaymentLogEntry
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


from mock import patch


# Mock create_payment so we don't need to call the external docdata service
def fake_create_payment(self):
    payment = self.MODEL_CLASS(order_payment=self.order_payment, **self.order_payment.integration_data)
    payment.total_gross_amount = self.order_payment.amount
    payment.payment_cluster_key = 'abc123'
    payment.payment_cluster_id = 'abc123'
    payment.save()

    return payment


class PaymentsDocdataTestCase(TestCase, FsmTestMixin):

    @patch.object(DocdataClient, 'create')
    def setUp(self, mock_client_create):
        # Mock response to creating the payment at docdata
        mock_client_create.return_value = {'order_key': 123, 'order_id': 123}

        # Mock create payment
        mock_create_payment = patch.object(DocdataPaymentAdapter, 'create_payment', fake_create_payment)

        self.order = OrderFactory.create()
        self.order_payment = OrderPaymentFactory.create(order=self.order, payment_method='docdata')
        self.service = PaymentService(order_payment=self.order_payment)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_authorized_status(self, mock_fetch_status, mock_transaction):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response('AUTHORIZED')

        self.service.check_payment_status()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment, StatusDefinition.AUTHORIZED)
        self.assert_status(self.order_payment, StatusDefinition.AUTHORIZED)
        self.assert_status(self.order, StatusDefinition.SUCCESS)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_no_payment_method_change(self, mock_fetch_status, mock_transaction):
        self.assertEquals(PaymentLogEntry.objects.count(), 2)

        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response('AUTHORIZED')

        order = OrderFactory.create()
        order_payment = OrderPaymentFactory.create(order=order, payment_method='docdataCreditcard')
        docdata_payment = DocdataPaymentFactory.create(order_payment=order_payment,
                                                       payment_cluster_id='1234',
                                                       total_gross_amount=100)
        docdata_transaction = DocdataTransactionFactory.create(payment=docdata_payment, payment_method='VISA')
        c = Client()
        resp = c.get(reverse('docdata-payment-status-update', kwargs={'payment_cluster_id': docdata_payment.payment_cluster_id}))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, 'success')

        # Reload the order payment
        order_payment = OrderPayment.objects.get(id=order_payment.id)
        self.assertEqual(order_payment.payment_method, 'docdataCreditcard')

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_payment_method_change(self, mock_fetch_status, mock_transaction):
        # Two payment log entries already exist: 2x 'a new payment status "started" '  
        self.assertEquals(PaymentLogEntry.objects.count(), 2)

        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response('AUTHORIZED')

        order = OrderFactory.create()
        # Ensure that we use an existing payment_method or the adapter throws an exception
        order_payment = OrderPaymentFactory.create(order=order, payment_method='docdataPaypal')
        docdata_payment = DocdataPaymentFactory.create(order_payment=order_payment,
                                                       payment_cluster_id='1235',
                                                       total_gross_amount=100)

        docdata_transaction = DocdataTransactionFactory.create(payment=docdata_payment, payment_method='VISA')
        c = Client()
        resp = c.get(reverse('docdata-payment-status-update', kwargs={'payment_cluster_id': docdata_payment.payment_cluster_id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, 'success')

        # # Reload the order payment
        order_payment = OrderPayment.objects.get(id=order_payment.id)
        self.assertEqual(order_payment.payment_method, 'docdataCreditcard')

        # Check that all is logged correctly
        self.assertEquals(PaymentLogEntry.objects.filter(payment=docdata_payment).count(), 6) # The status changes triggers the
                                                                                              # creation of more payment log entries
        log = PaymentLogEntry.objects.all()[0]
        self.assertEqual(log.message, 
            "{0} - Payment method changed for payment with id {1} and order payment with id {2}.".format(docdata_payment, docdata_payment.id,
                                                                                                    docdata_payment.order_payment.id))
        self.assertEqual(log.payment.id, docdata_payment.id)
        self.assertEqual(log.level, 'INFO')

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_unknown_payment_method_change(self, mock_fetch_status, mock_transaction):
        # Two payment log entries already exist: 2x 'a new payment status "started" '  
        self.assertEquals(PaymentLogEntry.objects.count(), 2)

        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response('AUTHORIZED')

        order = OrderFactory.create()
        # Ensure that we use an existing payment_method or the adapter throws an exception
        order_payment = OrderPaymentFactory.create(order=order, payment_method='docdataPaypal')
        docdata_payment = DocdataPaymentFactory.create(order_payment=order_payment,
                                                       payment_cluster_id='1236',
                                                       total_gross_amount=100)

        docdata_transaction = DocdataTransactionFactory.create(payment=docdata_payment, payment_method='BLABLABLA')
        c = Client()
        resp = c.get(reverse('docdata-payment-status-update', kwargs={'payment_cluster_id': docdata_payment.payment_cluster_id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, 'success')

        # Reload the order payment
        order_payment = OrderPayment.objects.get(id=order_payment.id)
        self.assertEqual(order_payment.payment_method, 'unknown')

        # Check that all is logged correctly
        self.assertEquals(PaymentLogEntry.objects.filter(payment=docdata_payment).count(), 6) # The status changes triggers the
                                                                                              # creation of more payment log entries
        log = PaymentLogEntry.objects.all()[0]
        self.assertEqual(log.message, 
            "{0} - Payment method changed for payment with id {1} and order payment with id {2}.".format(docdata_payment, docdata_payment.id,
                                                                                                    docdata_payment.order_payment.id))
        self.assertEqual(log.payment.id, docdata_payment.id)
        self.assertEqual(log.level, 'INFO')

