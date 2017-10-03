import factory
from moneyed.classes import Money, USD

from bluebottle.test.factory_models.payments import OrderPaymentFactory, OrderFactory

from ..models import ExternalPayment


class TelesomOrderFactory(OrderFactory):
    total = Money(10, USD)


class ExternalOrderPaymentFactory(OrderPaymentFactory):
    payment_method = 'externalLegacy'
    order = factory.SubFactory(TelesomOrderFactory)
    amount = Money(2000, USD)


class ExternalPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ExternalPayment
    order_payment = factory.SubFactory(ExternalOrderPaymentFactory)
