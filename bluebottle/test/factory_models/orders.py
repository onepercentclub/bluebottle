import factory

from bluebottle.utils.model_dispatcher import get_order_model

from .accounts import BlueBottleUserFactory

ORDER_MODEL = get_order_model()


class OrderFactory(factory.DjangoModelFactory):
    FACTORY_FOR = ORDER_MODEL

    user = factory.SubFactory(BlueBottleUserFactory)
    status = ORDER_MODEL.OrderStatuses.new
