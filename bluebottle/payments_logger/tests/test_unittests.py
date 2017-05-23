from mock import patch

from bluebottle.payments_logger.adapters import PaymentLogAdapter
from bluebottle.payments.services import PaymentService
from bluebottle.payments_docdata.adapters import DocdataPaymentAdapter
from bluebottle.payments_logger.models import PaymentLogEntry
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase, FsmTestMixin


class TestPaymentLogger(BluebottleTestCase, FsmTestMixin):
    @patch('bluebottle.payments_docdata.adapters.gateway.DocdataClient')
    def setUp(self, mock_client):
        super(TestPaymentLogger, self).setUp()

        # Mock response to creating the payment at docdata
        instance = mock_client.return_value
        instance.create.return_value = {'order_key': 123, 'order_id': 123}

        self.order = OrderFactory.create(total=35)
        self.order_payment = OrderPaymentFactory.create(
            payment_method='docdataIdeal', order=self.order,
            integration_data={'default_pm': 'ideal'})
        self.service = PaymentService(self.order_payment)

    def test_create_payment_create_log(self):
        """
        This test will start the process of creating a new payment and tests if
        a log associated has been created
        """
        # Get the number of logs in the table
        last_log = PaymentLogEntry.objects.all().order_by('-timestamp')[:1][0]

        # The latest entry should be for the payment associated with this test
        self.assertEqual(last_log.payment_id, self.order_payment.payment.id)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    @patch.object(DocdataPaymentAdapter, '_fetch_status')
    def test_check_authorized_status_logged(self, mock_fetch_status,
                                            mock_transaction):
        # Mock the status check with docdata
        mock_fetch_status.return_value = self.create_status_response(
            'AUTHORIZED',
            totals={'totalAcquirerApproved': '1000', 'totalRegistered': '1000'}
        )
        self.service.check_payment_status()

        last_log = PaymentLogEntry.objects.all().order_by('-timestamp')[:1][0]

        # Check that the status change was logged
        self.assertEqual(last_log.payment_id, self.order_payment.payment.id)
        self.assertEqual(last_log.message,
                         'DocdataPayment object - a new payment status authorized')
        self.assertEqual(last_log.level, 'INFO')


class TestPaymentLoggerAdapter(BluebottleTestCase):
    @patch('bluebottle.payments_docdata.adapters.gateway.DocdataClient')
    def setUp(self, mock_client):
        super(TestPaymentLoggerAdapter, self).setUp()

        # Mock response to creating the payment at docdata
        instance = mock_client.return_value
        instance.create.return_value = {'order_key': 123, 'order_id': 123}

        self.order = OrderFactory.create()
        self.order_payment = OrderPaymentFactory.create(
            payment_method='docdata', order=self.order,
            integration_data={'default_pm': 'ideal'})
        self.service = PaymentService(self.order_payment)

        PaymentLogEntry.objects.all().delete()

    def test_payment_log_adapter(self):
        """
        Tests the adapter creating different log messages
        """
        payment = self.order_payment.payment
        payment_logger = PaymentLogAdapter()

        payment_logger.log(payment=payment,
                           level='ERROR',
                           message='Test Error log')
        payment_logger.log(payment=payment,
                           level='INFO',
                           message='Test Info log')
        payment_logger.log(payment=payment,
                           level='WARN',
                           message='Test Warn log')

        self.assertEqual(3, PaymentLogEntry.objects.all().count())
