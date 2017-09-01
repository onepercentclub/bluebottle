import factory

from bluebottle.payments.models import Payment, OrderPayment
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
