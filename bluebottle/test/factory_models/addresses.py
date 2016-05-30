import factory

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.bb_accounts.models import UserAddress


class BlueBottleAddressFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = UserAddress

    user = factory.SubFactory(BlueBottleUserFactory)
