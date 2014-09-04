from django.test import TestCase
import time
from bluebottle.payments_logger.adapters import PaymentLogAdapter
from bluebottle.test.factory_models.payments import OrderPaymentFactory, PaymentFactory
from bluebottle.payments.services import PaymentService
from bluebottle.payments.models import Payment
from bluebottle.payments_docdata.gateway import DocdataClient
from bluebottle.payments_logger.models import PaymentLogEntry
from mock import patch
from bluebottle.test.factory_models.orders import OrderFactory


class TestPaymentLogger(TestCase):

    def setUp(self):
        self.order = OrderFactory.create()
        self.order_payment = OrderPaymentFactory.create(payment_method='docdata', order=self.order)

    @patch.object(DocdataClient, 'create')
    def test_create_payment_create_log(self, mock_client_create):
        """
        This test will start the process of creating a new payment and tests if
        a log associated has been created
        """
        # Mock the result for the DocdataClient (called from the PaymentService)
        mock_client_create.return_value = {'order_key': 123, 'order_id': 123}

        # Number of logs we have before starting the tests
        before_logs = PaymentLogEntry.objects.all()
        before_number = len(before_logs)

        # This will trigger the creation of an Adapter based on the order_payment passed
        # In this case a docdata payment adapter since the payment_method has been set to 'docdata'
        # The DocdataPaymentAdapter will than instantiate a PaymentAdapterLog 'payment.docdata'
        # If there are no Payment associated with the order_payment passed, the adapter will create a new payment
        # which will trigger the creation of a PaymentLogEntry.
        PaymentService(self.order_payment)

        # # Retrieve the PaymentLogEntry we just create
        # log = PaymentLogEntry.objects.get(payment=payment.id)

        # Get the number of logs in the table
        after_logs = PaymentLogEntry.objects.all()
        after_number = len(after_logs)

        # We expect to have one log more than before
        self.assertEqual(before_number + 1, after_number, 'before we had {0} logs, now we have {0} logs'
                         .format(after_number, after_number))

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
