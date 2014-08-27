import factory
from bluebottle.payments.models import OrderPayment
from bluebottle.test.factory_models.orders import OrderFactory

class OrderPaymentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = OrderPayment

    order = factory.SubFactory(OrderFactory)