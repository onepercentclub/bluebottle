from bluebottle.test.utils import BluebottleTestCase, FsmTestMixin
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory

from bluebottle.payments.services import PaymentService
from bluebottle.payments.exception import PaymentException
from bluebottle.utils.utils import StatusDefinition


class AdapterTestCase(BluebottleTestCase, FsmTestMixin):
    def setUp(self):
        self.user = BlueBottleUserFactory.create(can_pledge=True)

        self.order = OrderFactory.create(user=self.user)
        self.order_payment = OrderPaymentFactory.create(
            order=self.order, user=self.user, payment_method='pledgeStandard'
        )

    def test_order_status_cannot_pledge(self):
        """
        Normal user can not pledge
        """
        self.user.can_pledge = False
        self.user.save()

        with self.assertRaises(PaymentException):
            self.service = PaymentService(order_payment=self.order_payment)

    def test_order_status_can_pledge(self):
        """
        User with can_pledge setting enabled is allowed to pledge
        """
        PaymentService(order_payment=self.order_payment)

        # Check that the status propagated through to order
        self.assert_status(self.order, StatusDefinition.PLEDGED)

    def test_refund(self):
        """
        User with can_pledge setting enabled is allowed to pledge
        """
        service = PaymentService(order_payment=self.order_payment)

        service.refund_payment()

        # Check that the status propagated through to order
        self.assert_status(self.order_payment, StatusDefinition.REFUNDED)
