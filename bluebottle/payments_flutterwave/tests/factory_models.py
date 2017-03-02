import factory
from moneyed.classes import Money, NGN

from bluebottle.test.factory_models.payments import OrderPaymentFactory, OrderFactory

from ..models import FlutterwavePayment


class FlutterwaveOrderFactory(OrderFactory):
    total = Money(2000, NGN)


class FlutterwaveOrderPaymentFactory(OrderPaymentFactory):
    payment_method = 'flutterwaveVerve'
    order = factory.SubFactory(FlutterwaveOrderFactory)
    amount = Money(2000, NGN)


class FlutterwavePaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = FlutterwavePayment
    order_payment = factory.SubFactory(FlutterwaveOrderPaymentFactory)
