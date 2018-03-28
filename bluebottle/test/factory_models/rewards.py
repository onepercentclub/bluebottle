import factory

from bluebottle.rewards.models import Reward
from bluebottle.test.factory_models.projects import ProjectFactory


class RewardFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Reward

    project = factory.SubFactory(ProjectFactory)
    title = factory.Sequence(lambda n: 'Reward_{0}'.format(n))
    description = factory.Sequence(lambda n: 'Just some nice reward. No {0}'.format(n))
    amount = 50
    limit = 0
