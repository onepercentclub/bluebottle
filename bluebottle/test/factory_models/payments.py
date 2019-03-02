import factory

from bluebottle.payments.models import Payment, OrderPayment
from bluebottle.payments_mock.models import MockPayment
from .orders import OrderFactory


class OrderPaymentFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = OrderPayment

    payment_method = 'mock'
    order = factory.SubFactory(OrderFactory)


class PaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Payment

    order_payment = factory.SubFactory(OrderPaymentFactory)


class MockPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = MockPayment

    order_payment = factory.SubFactory(OrderPaymentFactory)
