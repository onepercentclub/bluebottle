import factory
from moneyed.classes import Money, XOF

from bluebottle.test.factory_models.payments import OrderPaymentFactory, OrderFactory

from ..models import VitepayPayment
from ..models import VitepayPayment


class VitepayOrderFactory(OrderFactory):
    total = Money(2000, XOF)


class VitepayOrderPaymentFactory(OrderPaymentFactory):
    payment_method = 'vitepayOrangemoney'
    order = factory.SubFactory(VitepayOrderFactory)
    amount = Money(2000, XOF)


class VitepayPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = VitepayPayment

    order_id = factory.Sequence(lambda n: 'opc-{0}'.format(n))
    order_payment = factory.SubFactory(VitepayOrderPaymentFactory)
