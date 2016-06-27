from bluebottle.test.utils import BluebottleTestCase, FsmTestMixin
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory

from bluebottle.payments.services import PaymentService
from bluebottle.payments.exception import PaymentException
from bluebottle.payments_pledge.adapters import PledgePaymentAdapter
from bluebottle.utils.utils import StatusDefinition


class AdapterTestCase(BluebottleTestCase, FsmTestMixin):
    def test_order_status_cannot_pledge(self):
        """
        Normal user can not pledge
        """
        user = BlueBottleUserFactory()

        order = OrderFactory.create(user=user)
        order_payment = OrderPaymentFactory.create(
            order=order, user=user, payment_method='pledgeStandard'
        )

        with self.assertRaises(PaymentException):
            self.service = PaymentService(order_payment=order_payment)

    def test_order_status_can_pledge(self):
        """
        User with can_pledge setting enabled is allowed to pledge
        """
        user = BlueBottleUserFactory(can_pledge=True)

        order = OrderFactory.create(user=user)
        order_payment = OrderPaymentFactory.create(
            order=order, user=user, payment_method='pledgeStandard'
        )
        service = PaymentService(order_payment=order_payment)

        # Check that the status propagated through to order
        self.assert_status(order, StatusDefinition.PLEDGED)
