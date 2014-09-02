from django.test import TestCase
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.utils.model_dispatcher import get_project_model, get_project_phaselog_model
from bluebottle.payments.services import PaymentService
from bluebottle.payments.models import Payment
from bluebottle.payments_docdata.gateway import DocdataClient
from mock import patch

PROJECT_MODEL = get_project_model()
PROJECT_PHASE_LOG_MODEL = get_project_phaselog_model()


class TestPaymentLogger(TestCase):

    @patch.object(DocdataClient, 'create')
    def setUp(self, mock_client_create):

        mock_client_create.return_value = {'order_key': 123, 'order_id': 123}
        self.order_payment = OrderPaymentFactory.create(payment_method='docdata')
        self.service = PaymentService(self.order_payment)


    def test_create_payment_log(self):

        # with self.assertRaises(Exception):
        import ipdb; ipdb.set_trace()
        log_number = PROJECT_PHASE_LOG_MODEL.objects.get(payment=Payment.objects.get(order_payment=self.order_payment)).count()
        self.assertEqual(1, log_number, 'instead there are {0}'.format(log_number))


        # self.assertEqual(before_num_of_logs + 1, PROJECT_PHASE_LOG_MODEL.objects.count(), "The Payment Adapter method"
        #                                                                                   "create_payment should create"
        #                                                                                   "a payment log")


