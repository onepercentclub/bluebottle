import factory

from bluebottle.rewards.models import Reward


class RewardFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Reward

    title = factory.Sequence(lambda n: 'Reward_{0}'.format(n))
    description = factory.Sequence(lambda n: 'Just some nice reward. No {0}'.format(n))
    amount = 50
    limit = 0
