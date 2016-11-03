import factory
from moneyed.classes import Money, XOF

from bluebottle.test.factory_models.payments import OrderPaymentFactory, OrderFactory

from ..models import InterswitchPayment


class InterswitchOrderFactory(OrderFactory):
    total = Money(2000, XOF)


class InterswitchOrderPaymentFactory(OrderPaymentFactory):
    payment_method = 'interswitchOrangemoney'
    order = factory.SubFactory(InterswitchOrderFactory)
    amount = Money(2000, XOF)


class InterswitchPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = InterswitchPayment

    order_payment = factory.SubFactory(InterswitchOrderPaymentFactory)
