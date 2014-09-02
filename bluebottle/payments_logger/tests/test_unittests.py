from django.test import TestCase
from bluebottle.payments_docdata.adapters import DocdataPaymentAdapter
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.utils.model_dispatcher import get_project_model, get_project_phaselog_model

PROJECT_MODEL = get_project_model()
PROJECT_PHASE_LOG_MODEL = get_project_phaselog_model()


class TestPaymentLogger(TestCase):

    def setUp(self):

        self.order_payment = OrderPaymentFactory.create()
        self.docdata_adapter = DocdataPaymentAdapter(self.order_payment)


    def test_create_payment_log(self):
        before_num_of_logs = PROJECT_PHASE_LOG_MODEL.objects.count()
        self.docdata_adapter.create_payment()
        self.assertEqual(before_num_of_logs + 1, PROJECT_PHASE_LOG_MODEL.objects.count(), "The Payment Adapter method"
                                                                                          "create_payment should create"
                                                                                          "a payment log")


