from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
import factory
from bluebottle.test.models import TestAddress


class BlueBottleAddressFactory(factory.DjangoModelFactory):
    FACTORY_FOR = TestAddress
    user = factory.SubFactory(BlueBottleUserFactory)
