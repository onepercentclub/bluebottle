import factory

from bluebottle.orders.models import Order
from bluebottle.utils.utils import StatusDefinition
from bluebottle.payments.models import OrderPaymentAction
from .accounts import BlueBottleUserFactory


class OrderFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Order
    user = factory.SubFactory(BlueBottleUserFactory)
    status = StatusDefinition.CREATED


class OrderActionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = OrderPaymentAction
