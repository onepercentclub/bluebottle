import factory

from bluebottle.orders.models import Order
from bluebottle.utils.utils import StatusDefinition
from bluebottle.payments.models import OrderPaymentAction

from djmoney.money import Money

from .accounts import BlueBottleUserFactory


class OrderFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Order
    user = factory.SubFactory(BlueBottleUserFactory)
    status = StatusDefinition.CREATED
    total = Money(0, 'EUR')


class OrderActionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = OrderPaymentAction
