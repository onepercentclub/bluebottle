from bluebottle.projects.models import ProjectPhase
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.utils import BluebottleTestCase
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
        self.order_payment.save()
        self.assertEqual(self.order.status, StatusDefinition.LOCKED,
                         'Starting an Order Payment should change Order to locked')

        # Set the associated order payment to authorized
        self.order_payment.authorized()
        self.order_payment.save()
        self.assertEqual(self.order.status, StatusDefinition.PENDING,
                         'Authorizing an Order Payment should change Order to pending.')

        # Set the associated order payment to settled
        self.order_payment.settled()
        self.order_payment.save()
        self.assertEqual(self.order.status, StatusDefinition.SUCCESS,
                         'Settling an Order Payment should change Order to success')

    def test_basic_order_failed_flow(self):
        # Set the associated order payment to started
        self.order_payment.started()
        self.order_payment.save()
        self.assertEqual(self.order.status, StatusDefinition.LOCKED,
                         'Starting an Order Payment should change Order to locked')

        self.order_payment.cancelled()
        self.order_payment.save()
        self.assertEqual(self.order.status, StatusDefinition.FAILED,
                         'Cancelling an Order Payment should change Order to failed')

    def test_oneway_order_status(self):
        self.order_payment.started()
        self.order_payment.save()
        self.assertEqual(self.order_payment.status, StatusDefinition.STARTED)

        # Set the Order to cancelled
        self.order.success()
        self.order.save()
        self.assertEqual(self.order_payment.status, StatusDefinition.STARTED,
                         'Changing the Order status should not change the Order Payment status')

    def test_refunded(self):
        DonationFactory.create(order=self.order)
        self.order_payment.started()

        self.order_payment.save()

        self.order_payment.authorized()
        self.order_payment.save()

        self.order_payment.refunded()
        self.assertEqual(self.order.refund_type, 'one-off')

    def test_refund_project(self):
        donation = DonationFactory.create(order=self.order)
        donation.project.status = ProjectPhase.objects.get(slug='refunded')
        donation.project.save()
        self.order_payment.started()

        self.order_payment.save()

        self.order_payment.authorized()
        self.order_payment.save()

        self.order_payment.refunded()
        self.assertEqual(self.order.refund_type, 'project-refunded')


