import factory
from moneyed.classes import Money, KES

from bluebottle.test.factory_models.payments import OrderPaymentFactory, OrderFactory

from ..models import LipishaPayment


class LipishaOrderFactory(OrderFactory):
    total = Money(250, KES)


class LipishaOrderPaymentFactory(OrderPaymentFactory):
    payment_method = 'telesomZaad'
    order = factory.SubFactory(LipishaOrderFactory)
    amount = Money(250, KES)


class LipishaPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = LipishaPayment
    order_payment = factory.SubFactory(LipishaOrderPaymentFactory)
