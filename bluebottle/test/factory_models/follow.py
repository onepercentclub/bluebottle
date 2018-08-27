import factory

from bluebottle.bb_follow.models import Follow
from bluebottle.test.factory_models.projects import ProjectFactory
from .accounts import BlueBottleUserFactory


class FollowFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Follow
    user = factory.SubFactory(BlueBottleUserFactory)
    followed_object = factory.SubFactory(ProjectFactory)
