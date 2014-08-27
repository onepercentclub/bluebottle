import factory

from bluebottle.payments.models import Payment, OrderPayment

from .projects import ProjectFactory
from .accounts import BlueBottleUserFactory
from .orders import OrderFactory


class PaymentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Payment


class OrderPaymentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = OrderPayment

    amount = 100
    order = factory.SubFactory(OrderFactory)