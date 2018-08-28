import mock

from django.db import connection

from moneyed import Money

from bluebottle.projects.tasks import refund_project
from bluebottle.projects.models import ProjectPhase

from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.orders.models import Order
from bluebottle.payments.services import PaymentService
from bluebottle.payments_docdata.tests.factory_models import DocdataPaymentFactory
from bluebottle.payments_docdata.adapters import DocdataPaymentAdapter
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.projects import ProjectFactory

from bluebottle.test.utils import BluebottleTestCase


class TestRefund(BluebottleTestCase):
    def setUp(self):
        super(TestRefund, self).setUp()

        self.init_projects()

        self.project = ProjectFactory.create(status=ProjectPhase.objects.get(slug='refunded'))

        self.order = OrderFactory.create()
        self.order_payment = OrderPaymentFactory.create(
            order=self.order,
            payment_method='docdataIdeal',
            integration_data={'default_pm': 'ideal'},
        )
        payment = DocdataPaymentFactory.create(
            order_payment=self.order_payment,
            payment_cluster_key='123-4',
            default_pm='ideal',
            total_gross_amount=100
        )

        DonationFactory.create(
            project=self.project,
            order=self.order,
            amount=Money(100, 'EUR'),
        )
        payment.status = 'authorized'
        payment.save()
        payment.status = 'settled'
        payment.save()

        self.project.refresh_from_db()

    def mock_side_effect(self):
        self.order_payment.payment.status = 'refund_requested'
        self.order_payment.payment.save()

    def test_refund(self):
        self.assertEqual(
            self.project.amount_donated, Money(100, 'EUR')
        )

        with mock.patch.object(
            DocdataPaymentAdapter,
            'refund_payment',
            side_effect=self.mock_side_effect
        ) as refund:
            refund_project(connection.tenant, self.project)

        self.assertEqual(refund.call_count, 1)
        self.order = Order.objects.get(pk=self.order.pk)
        self.assertEqual(self.order.status, 'refund_requested')

        self.project.refresh_from_db()
        self.assertEqual(
            self.project.amount_donated, Money(0, 'EUR')
        )

        self.order_payment.payment.status = 'refunded'
        self.order_payment.payment.save()

        self.order = Order.objects.get(pk=self.order.pk)
        self.assertEqual(self.order.status, 'cancelled')

        self.project.refresh_from_db()
        self.assertEqual(
            self.project.amount_donated, Money(0, 'EUR')
        )

    def test_refund_pledged_payment(self):
        user = BlueBottleUserFactory.create(can_pledge=True)

        order = OrderFactory.create(user=user)
        order_payment = OrderPaymentFactory.create(
            order=order, user=user, payment_method='pledgeStandard'
        )
        DonationFactory.create(
            project=self.project,
            order=order,
            amount=Money(100, 'EUR'),
        )
        PaymentService(order_payment=order_payment)

        with mock.patch.object(
            DocdataPaymentAdapter,
            'refund_payment',
            side_effect=self.mock_side_effect
        ):
            refund_project(connection.tenant, self.project)

        order = Order.objects.get(pk=order.pk)
        self.assertEqual(order.status, 'cancelled')

    def test_refund_created_payment(self):
        order = OrderFactory.create()
        order_payment = OrderPaymentFactory.create(
            order=order,
            payment_method='docdataIdeal',
            integration_data={'default_pm': 'ideal'},
        )
        DocdataPaymentFactory.create(
            order_payment=order_payment,
            payment_cluster_key='456-4',
            payment_cluster_id='test',
            default_pm='ideal',
            total_gross_amount=100
        )

        DonationFactory.create(
            project=self.project,
            order=order,
            amount=Money(100, 'EUR'),
        )

        with mock.patch.object(
            DocdataPaymentAdapter,
            'refund_payment',
            side_effect=self.mock_side_effect
        ) as refund:
            refund_project(connection.tenant, self.project)

        self.order = Order.objects.get(pk=self.order.pk)
        self.assertEqual(refund.call_count, 1)
        self.assertEqual(self.order.status, 'refund_requested')

        self.order_payment.payment.status = 'refunded'
        self.order_payment.payment.save()

        self.order = Order.objects.get(pk=self.order.pk)
        self.assertEqual(self.order.status, 'cancelled')
