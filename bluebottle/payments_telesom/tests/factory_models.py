import factory
from moneyed.classes import Money, USD

from bluebottle.test.factory_models.payments import OrderPaymentFactory, OrderFactory

from ..models import TelesomPayment


class TelesomOrderFactory(OrderFactory):
    total = Money(10, USD)


class TelesomOrderPaymentFactory(OrderPaymentFactory):
    payment_method = 'telesomZaad'
    order = factory.SubFactory(TelesomOrderFactory)
    amount = Money(2000, USD)


class TelesomPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = TelesomPayment
    order_payment = factory.SubFactory(TelesomOrderPaymentFactory)
