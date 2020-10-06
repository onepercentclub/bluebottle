from builtins import object
import factory

from bluebottle.bb_follow.models import Follow
from bluebottle.initiatives.tests.factories import InitiativeFactory
from .accounts import BlueBottleUserFactory


class FollowFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Follow
    user = factory.SubFactory(BlueBottleUserFactory)
    followed_object = factory.SubFactory(InitiativeFactory)
