import factory

from bluebottle.follow.models import Follow
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class InitiativeFollowFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Follow
    user = factory.SubFactory(BlueBottleUserFactory)
    instance = factory.SubFactory(InitiativeFactory)
