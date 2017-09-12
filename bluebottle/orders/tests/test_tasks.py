from datetime import timedelta
import mock

from django.db import connection
from django.test.utils import override_settings
from django.utils import timezone

from bluebottle.orders.models import Order
from bluebottle.orders.tasks import timeout_new_order, timeout_locked_order

from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import PaymentFactory, OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import StatusDefinition


class TestOrderTimeout(BluebottleTestCase):
    def setUp(self):
        super(TestOrderTimeout, self).setUp()

        self.init_projects()

    @override_settings(CELERY_RESULT_BACKEND='amqp')
    def test_order_time_out(self):
        with mock.patch.object(timeout_new_order, 'apply_async') as apply_async:
            order = OrderFactory.create()
            args, kwargs = apply_async.call_args

            self.assertEqual(args[0], [order, connection.tenant])
            self.assertTrue(
                kwargs['eta'] - timezone.now() < timedelta(minutes=10)
            )
            self.assertTrue(
                kwargs['eta'] - timezone.now() > timedelta(minutes=9, seconds=59)
            )

    @override_settings(CELERY_RESULT_BACKEND='amqp')
    def test_order_time_out_called_once(self):
        with mock.patch.object(timeout_new_order, 'apply_async') as apply_async:
            order = OrderFactory.create()
            order.transition_to(StatusDefinition.LOCKED)
            order.save()

            apply_async.assert_called_once()

    @override_settings(CELERY_RESULT_BACKEND='amqp')
    def test_locked_order_timeout(self):
        with mock.patch.object(timeout_locked_order, 'apply_async') as apply_async:
            with mock.patch.object(timeout_new_order, 'apply_async'):
                order = OrderFactory.create()
                PaymentFactory.create(
                    order_payment=OrderPaymentFactory.create(order=order)
                )
                self.assertEqual(
                    order.status, StatusDefinition.LOCKED
                )

                args, kwargs = apply_async.call_args
                self.assertEqual(args[0], [order, connection.tenant])

                self.assertTrue(
                    kwargs['eta'] - timezone.now() < timedelta(hours=3)
                )
                self.assertTrue(
                    kwargs['eta'] - timezone.now() > timedelta(hours=2, minutes=59)
                )

    def test_timeout_task_new_order(self):
        order = OrderFactory.create()

        timeout_new_order(order, connection.tenant)

        order = Order.objects.get(pk=order.pk)

        self.assertEqual(order.status, StatusDefinition.FAILED)

    def test_task_timeout_new_order_locked(self):
        order = OrderFactory.create()
        order.transition_to(StatusDefinition.LOCKED)
        order.save()

        timeout_new_order(order, connection.tenant)

        order = Order.objects.get(pk=order.pk)

        self.assertEqual(order.status, StatusDefinition.LOCKED)

    def test_timeout_task_locked_order(self):
        order = OrderFactory.create(status=StatusDefinition.LOCKED)

        timeout_locked_order(order, connection.tenant)

        order = Order.objects.get(pk=order.pk)

        self.assertEqual(order.status, StatusDefinition.FAILED)

    def test_task_timeout_locked_order_settled(self):
        order = OrderFactory.create(status=StatusDefinition.LOCKED)
        order.transition_to(StatusDefinition.SUCCESS)
        order.save()

        timeout_locked_order(order, connection.tenant)

        order = Order.objects.get(pk=order.pk)

        self.assertEqual(order.status, StatusDefinition.SUCCESS)
