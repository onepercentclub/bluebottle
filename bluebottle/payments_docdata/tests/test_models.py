from bluebottle.test.factory_models.addresses import BlueBottleAddressFactory
from bluebottle.test.factory_models.geo import CountryFactory
from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse

from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import FsmTestMixin

from bluebottle.payments.services import PaymentService
from bluebottle.payments_docdata.gateway import DocdataClient
from bluebottle.payments_docdata.adapters import DocdataPaymentAdapter


from bluebottle.utils.utils import StatusDefinition
from bluebottle.payments_docdata.tests.factory_models import DocdataPaymentFactory, DocdataTransactionFactory
from bluebottle.payments.models import OrderPayment 
from bluebottle.payments_logger.models import PaymentLogEntry


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
        self.order_payment = OrderPaymentFactory.create(order=self.order, payment_method='docdataIdeal',
                                                        integration_data={'default_pm': 'ideal'})
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
        self.assert_status(self.order, StatusDefinition.PENDING)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_no_payment_method_change(self, mock_fetch_status, mock_transaction):
        self.assertEquals(PaymentLogEntry.objects.count(), 2)

        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response('AUTHORIZED')

        order = OrderFactory.create()
        order_payment = OrderPaymentFactory.create(order=order, payment_method='docdataCreditcard')
        docdata_payment = DocdataPaymentFactory.create(order_payment=order_payment,
                                                       default_pm='mastercard',
                                                       payment_cluster_id='1234',
                                                       total_gross_amount=100)
        docdata_transaction = DocdataTransactionFactory.create(payment=docdata_payment, payment_method='VISA')
        c = Client()
        merchant_order_id = "{0}-1".format(order_payment.id)
        resp = c.get(reverse('docdata-payment-status-update', kwargs={'merchant_order_id': merchant_order_id}))

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
        mock_fetch_status.return_value = self.create_status_response('AUTHORIZED')

        order = OrderFactory.create()
        # Ensure that we use an existing payment_method or the adapter throws an exception
        order_payment = OrderPaymentFactory.create(order=order, payment_method='docdataPaypal')
        docdata_payment = DocdataPaymentFactory.create(order_payment=order_payment,
                                                       default_pm='paypal',
                                                       payment_cluster_id='1235',
                                                       total_gross_amount=100)

        docdata_transaction = DocdataTransactionFactory.create(payment=docdata_payment, payment_method='VISA')
        c = Client()
        merchant_order_id = "{0}-1".format(order_payment.id)
        resp = c.get(reverse('docdata-payment-status-update', kwargs={'merchant_order_id': merchant_order_id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, 'success')

        # # Reload the order payment
        order_payment = OrderPayment.objects.get(id=order_payment.id)
        self.assertEqual(order_payment.payment_method, 'docdataPaypal')

        # Check that all is logged correctly
        self.assertEquals(PaymentLogEntry.objects.filter(payment=docdata_payment).count(), 5) # The status changes triggers the
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
        self.skipTest('Skipping test until we update it.')

        # Two payment log entries already exist: 2x 'a new payment status "started" '
        self.assertEquals(PaymentLogEntry.objects.count(), 2)

        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response('AUTHORIZED')

        order = OrderFactory.create()
        # Ensure that we use an existing payment_method or the adapter throws an exception
        order_payment = OrderPaymentFactory.create(order=order, payment_method='docdataPaypal')
        docdata_payment = DocdataPaymentFactory.create(order_payment=order_payment,
                                                       default_pm='paypal',
                                                       payment_cluster_id='1236',
                                                       total_gross_amount=100)


        docdata_transaction = DocdataTransactionFactory.create(payment=docdata_payment, payment_method='BLABLABLA')
        c = Client()
        merchant_order_id = "{0}-1".format(order_payment.id)
        resp = c.get(reverse('docdata-payment-status-update', kwargs={'merchant_order_id': merchant_order_id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, 'success')

        # Reload the order payment
        order_payment = OrderPayment.objects.get(id=order_payment.id)
        self.assertEqual(order_payment.payment_method, 'docdataPaypal')

        # Check that all is logged correctly
        self.assertEquals(PaymentLogEntry.objects.filter(payment=docdata_payment).count(), 5)
        log = PaymentLogEntry.objects.all()[0]
        self.assertEqual(log.message,
            "{0} - Payment method '{1}' not found for payment with id {2} and order payment with id {3}.".format(
                docdata_payment,
                'BLABLABLA',
                docdata_payment.id,
                docdata_payment.order_payment.id))
        self.assertEqual(log.payment.id, docdata_payment.id)
        self.assertEqual(log.level, 'WARNING')


class AdapterTestCase(TestCase):
    def setUp(self):
        pass

    @patch.object(DocdataClient, 'create')
    def test_incomplete_userdata(self, mock_client_create):
        mock_client_create.return_value = {'order_key': 123, 'order_id': 123}
        mock_create_payment = patch.object(DocdataPaymentAdapter, 'create_payment', fake_create_payment)

        user = BlueBottleUserFactory()
        address = BlueBottleAddressFactory(user=user)
        self.order = OrderFactory.create(user=user)
        self.order_payment = OrderPaymentFactory.create(order=self.order, payment_method='docdataIdeal',
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

    @patch.object(DocdataClient, 'create')
    def test_normal_userdata(self, mock_client_create):
        mock_client_create.return_value = {'order_key': 123, 'order_id': 123}
        mock_create_payment = patch.object(DocdataPaymentAdapter, 'create_payment', fake_create_payment)

        user = BlueBottleUserFactory()
        holland = CountryFactory(name='Netherlands', alpha2_code='NL')

        address = BlueBottleAddressFactory(user=user, line1='Dam 1a', line2='Bovenste bel', city='Amsterdam',
                                           postal_code='1000AA', country=holland)

        self.order = OrderFactory.create(user=user)
        self.order_payment = OrderPaymentFactory.create(order=self.order, payment_method='docdataIdeal',
                                                        integration_data={'default_pm': 'ideal'})

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

