from bluebottle.payments.services import PaymentService
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.utils import FsmTestMixin, BluebottleTestCase
from bluebottle.utils.utils import StatusDefinition


class PaymentsMockTestCase(BluebottleTestCase, FsmTestMixin):
    def setUp(self):
        super(PaymentsMockTestCase, self).setUp()

        self.init_projects()

        self.order = OrderFactory.create(total=35)
        self.order_payment = OrderPaymentFactory.create(order=self.order,
                                                        payment_method='mock')
        self.service = PaymentService(order_payment=self.order_payment)

    def test_check_authorized_status(self):
        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment, StatusDefinition.STARTED)
        self.assert_status(self.order_payment, StatusDefinition.STARTED)
        self.assert_status(self.order, StatusDefinition.LOCKED)
