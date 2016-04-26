from bluebottle.test.utils import BluebottleTestCase, FsmTestMixin
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory

from bluebottle.payments.services import PaymentService
from bluebottle.payments_pledge.adapters import PledgePaymentAdapter
from bluebottle.utils.utils import StatusDefinition


class AdapterTestCase(BluebottleTestCase, FsmTestMixin):
    def test_order_status(self):
        user = BlueBottleUserFactory()

        self.order = OrderFactory.create(user=user)
        self.order_payment = OrderPaymentFactory.create(order=self.order,
                                                        payment_method='pledgeStandard')

        self.service = PaymentService(order_payment=self.order_payment)

        # Check that the status propagated through to order
        self.assert_status(self.order, StatusDefinition.SUCCESS)
