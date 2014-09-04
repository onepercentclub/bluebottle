from datetime import datetime

from django.test import TestCase
from django_fsm.db.fields import TransitionNotAllowed

from bluebottle.test.factory_models.payments import PaymentFactory, OrderPaymentFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.models import TestBaseUser
from bluebottle.test.utils import FsmTestMixin

from bluebottle.payments.services import PaymentService
from bluebottle.payments_docdata.gateway import DocdataClient
from bluebottle.payments_docdata.adapters import DocdataPaymentAdapter

from bluebottle.utils.utils import StatusDefinition

from mock import patch


# Mock create_payment so we don't need to call the external docdata service
def fake_create_payment(self):
    payment = self.MODEL_CLASS(order_payment=self.order_payment, **self.order_payment.integration_data)
    payment.total_gross_amount = self.order_payment.amount
    payment.payment_cluster_key = 'abc123'
    payment.payment_cluster_id = 'abc123'
    payment.save()

    return payment

# Basic mock to set the status to authorized on a payment without fetching 
# from external docdata service.
def fake_authorized_status(self):
    status = self.get_status_mapping('AUTHORIZED')
    self.payment.status = status
    self.payment.save()


class PaymentsDocdataTestCase(TestCase, FsmTestMixin):

    @patch.object(DocdataClient, 'create')
    def setUp(self, mock_client_create):
        # Mock response to creating the payment at docdata
        mock_client_create.return_value = {'order_key': 123, 'order_id': 123}

        mock_create_payment = patch.object(DocdataPaymentAdapter, 'create_payment', fake_create_payment)
        with mock_create_payment:
            self.order = OrderFactory.create()
            self.order_payment = OrderPaymentFactory.create(order=self.order, payment_method='docdata')
            self.service = PaymentService(order_payment=self.order_payment)

    @patch.object(DocdataPaymentAdapter, '_store_payment_transaction')
    def test_check_authorized_status(self, mock_transaction):
        # Mock the status check with docdata
        mock_check_payment_status = patch.object(DocdataPaymentAdapter, 'check_payment_status', fake_authorized_status)
        with mock_check_payment_status:
            self.service.check_payment_status()

            # Check that the status propagated through to order
            self.assert_status(self.order_payment.payment, StatusDefinition.AUTHORIZED)
            self.assert_status(self.order_payment, StatusDefinition.AUTHORIZED)
            self.assert_status(self.order, StatusDefinition.SUCCESS)
