from django.test import TestCase
import time

from mock import patch

from bluebottle.payments_logger.adapters import PaymentLogAdapter
from bluebottle.test.factory_models.payments import OrderPaymentFactory, PaymentFactory
from bluebottle.payments.services import PaymentService
from bluebottle.payments.models import Payment
from bluebottle.payments_docdata.gateway import DocdataClient
from bluebottle.payments_docdata.adapters import DocdataPaymentAdapter
from bluebottle.payments_logger.models import PaymentLogEntry
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.utils import FsmTestMixin


class TestPaymentLogger(TestCase, FsmTestMixin):

    @patch.object(DocdataClient, 'create')
    def setUp(self, mock_client_create):
        mock_client_create.return_value = {'order_key': 123, 'order_id': 123}

        self.order = OrderFactory.create()
        self.order_payment = OrderPaymentFactory.create(payment_method='docdata', order=self.order)
        self.service = PaymentService(self.order_payment)

    def test_create_payment_create_log(self):
        """
        This test will start the process of creating a new payment and tests if
        a log associated has been created
        """
        # Get the number of logs in the table
        last_log = PaymentLogEntry.objects.all().order_by('-timestamp')[:1][0]

        # We expect to have one log more than before
        self.assertEqual(last_log.payment_id, self.order_payment.payment.id)


    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_authorized_status_logged(self, mock_fetch_status, mock_transaction):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response('AUTHORIZED')
        self.service.check_payment_status()

        last_log = PaymentLogEntry.objects.all().order_by('-timestamp')[:1][0]

        # Check that the status propagated through to order
        self.assertEqual(last_log.payment_id, self.order_payment.payment.id)
        self.assertEqual(last_log.message, 'a new payment status authorized')
        self.assertEqual(last_log.level, 'info')
        

class TestPaymentLoggerAdapter(TestCase):

    def setUp(self):
        self.order = OrderFactory.create()
        self.order_payment = OrderPaymentFactory.create(payment_method='docdata', order=self.order)


    def test_payment_log_adapter(self):
        """
        Tests the adapter creating different log messages
        """
        payment = PaymentFactory.create(order_payment=self.order_payment)

        before_logs = PaymentLogEntry.objects.all()
        before_logs_num = len(before_logs)

        payment_logger = PaymentLogAdapter('payment.docdata')

        payment_logger.log(payment=payment,
                           level='error',
                           message='Test Error log')
        time.sleep(2)
        payment_logger.log(payment=payment,
                           level='info',
                           message='Test Info log')
        time.sleep(2)
        payment_logger.log(payment=payment,
                           level='warn',
                           message='Test Warn log')

        after_logs = PaymentLogEntry.objects.all()
        after_logs_num = len(after_logs)

        self.assertEqual(before_logs_num + 3, after_logs_num)

        # need to wait some time between creating the logs and before finishing the test
        # otherwise the messages won't be sent (or the rate will be to high) and an error will occur
        time.sleep(5)
