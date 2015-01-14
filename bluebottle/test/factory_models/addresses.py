import factory

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.members.models import UserAddress


class BlueBottleAddressFactory(factory.DjangoModelFactory):
    FACTORY_FOR = UserAddress
    user = factory.SubFactory(BlueBottleUserFactory)
