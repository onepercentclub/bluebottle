from moneyed import Money

from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import StatusDefinition


class TestOrderUpdateProjectAmount(BluebottleTestCase):
    def setUp(self):
        self.order = OrderFactory.create()
        self.project = ProjectFactory.create(
            amount_asked=1000
        )
        self.donation = DonationFactory.create(
            amount=1000, project=self.project, order=self.order
        )

        self.order.transition_to(StatusDefinition.LOCKED)
        self.order.save()
        super(TestOrderUpdateProjectAmount, self).setUp()

    def test_order_pending(self):
        self.assertEqual(
            self.project.amount_donated, Money(0, 'EUR')
        )

        self.order.transition_to(StatusDefinition.PENDING)
        self.order.save()
        self.project.refresh_from_db()

        self.assertEqual(
            self.project.amount_donated, Money(1000, 'EUR')
        )

    def test_order_pending_then_failed(self):
        self.assertEqual(
            self.project.amount_donated, Money(0, 'EUR')
        )

        self.order.transition_to(StatusDefinition.PENDING)
        self.order.save()
        self.order.transition_to(StatusDefinition.FAILED)
        self.order.save()

        self.project.refresh_from_db()

        self.assertEqual(
            self.project.amount_donated, Money(0, 'EUR')
        )

    def test_order_pending_then_refunded(self):
        self.assertEqual(
            self.project.amount_donated, Money(0, 'EUR')
        )

        self.order.transition_to(StatusDefinition.PENDING)
        self.order.save()
        self.order.transition_to(StatusDefinition.REFUNDED)
        self.order.save()

        self.project.refresh_from_db()

        self.assertEqual(
            self.project.amount_donated, Money(0, 'EUR')
        )
