import factory
import uuid

from bluebottle.utils.utils import ModelDispatcher

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

def random_order_number(length=30):
    return unicode(uuid.uuid4().hex)[0:length]

ORDER_MODEL = ModelDispatcher().get_order_model()

class OrderFactory(factory.DjangoModelFactory):
    FACTORY_FOR = ORDER_MODEL

    user = factory.SubFactory(BlueBottleUserFactory)
    # uuid = factory.LazyAttribute(lambda t: 3)
