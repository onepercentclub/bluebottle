from datetime import datetime

from bluebottle.test.utils import BluebottleTestCase
from django_fsm.db.fields import TransitionNotAllowed

from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.utils.utils import StatusDefinition


class BlueBottleOrderTestCase(BluebottleTestCase):
    
    def setUp(self):
        super(BlueBottleOrderTestCase, self).setUp()

        self.order = OrderFactory.create()
        self.order_payment = OrderPaymentFactory.create(order=self.order)

    def test_basic_order_flow(self):
        self.assertEqual(self.order.status, StatusDefinition.LOCKED,
            'Creating an Order Payment should change Order to locked')

        self.order_payment.started()
        self.assertEqual(self.order.status, StatusDefinition.LOCKED,
            'Starting an Order Payment should change Order to locked')

        # Set the associated order payment to authorized
        self.order_payment.authorized()
        self.assertEqual(self.order.status, StatusDefinition.PENDING,
            'Authorizing an Order Payment should change Order to pending.')

        # Set the associated order payment to settled
        self.order_payment.settled()
        self.assertEqual(self.order.status, StatusDefinition.SUCCESS,
            'Settling an Order Payment should change Order to success')
        
    def test_basic_order_failed_flow(self):
        # Set the associated order payment to started
        self.order_payment.started()
        self.assertEqual(self.order.status, StatusDefinition.LOCKED,
            'Starting an Order Payment should change Order to locked')

        self.order_payment.cancelled()
        self.assertEqual(self.order.status, StatusDefinition.FAILED,
            'Cancelling an Order Payment should change Order to failed')

    def test_oneway_order_status(self):
        self.order_payment.started()
        self.assertEqual(self.order_payment.status, StatusDefinition.STARTED)

        # Set the Order to cancelled
        self.order.succeeded()
        self.assertEqual(self.order_payment.status, StatusDefinition.STARTED,
            'Changing the Order status should not change the Order Payment status')


