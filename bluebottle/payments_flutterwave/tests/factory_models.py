import factory
from moneyed.classes import Money, NGN, KES

from bluebottle.test.factory_models.payments import OrderPaymentFactory, OrderFactory

from ..models import FlutterwavePayment, FlutterwaveMpesaPayment


class FlutterwaveOrderFactory(OrderFactory):
    total = Money(2000, NGN)


class FlutterwaveOrderPaymentFactory(OrderPaymentFactory):
    payment_method = 'flutterwaveCreditcard'
    order = factory.SubFactory(FlutterwaveOrderFactory)
    amount = Money(2000, NGN)


class FlutterwavePaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = FlutterwavePayment
    order_payment = factory.SubFactory(FlutterwaveOrderPaymentFactory)


class FlutterwaveMpesaOrderFactory(OrderFactory):
    total = Money(5000, KES)


class FlutterwaveMpesaOrderPaymentFactory(OrderPaymentFactory):
    payment_method = 'flutterwaveMpesa'
    order = factory.SubFactory(FlutterwaveMpesaOrderFactory)
    amount = Money(5000, KES)


class FlutterwaveMpesaPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = FlutterwaveMpesaPayment
    order_payment = factory.SubFactory(FlutterwaveMpesaOrderPaymentFactory)
