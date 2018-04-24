import factory
from moneyed.classes import Money, UGX

from bluebottle.test.factory_models.payments import OrderPaymentFactory, OrderFactory

from ..models import BeyonicPayment


class BeyonicOrderFactory(OrderFactory):
    total = Money(50000, UGX)


class BeyonicOrderPaymentFactory(OrderPaymentFactory):
    payment_method = 'beyonicAirtel'
    order = factory.SubFactory(BeyonicOrderFactory)
    amount = Money(50000, UGX)


class BeyonicPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = BeyonicPayment

    transaction_reference = factory.Sequence(lambda n: 'bey-{0}'.format(n))
    order_payment = factory.SubFactory(BeyonicOrderPaymentFactory)
