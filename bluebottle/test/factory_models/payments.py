import factory

from bluebottle.payments.models import Payment, OrderPayment
from .orders import OrderFactory


class OrderPaymentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = OrderPayment

    amount = 100
    order = factory.SubFactory(OrderFactory)


class PaymentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Payment

    order_payment = factory.SubFactory(OrderPaymentFactory)
