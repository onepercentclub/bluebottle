from builtins import object

import factory.fuzzy
from pytz import UTC

from bluebottle.collect.models import CollectActivity, CollectContributor
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class CollectActivityFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = CollectActivity

    title = factory.Faker('sentence')
    slug = factory.Faker('slug')
    description = factory.Faker('text')

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    start = factory.Faker('future_date', end_date="+20d", tzinfo=UTC)
    end = factory.Faker('future_date', end_date="+2d", tzinfo=UTC)


class CollectContributorFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = CollectContributor

    activity = factory.SubFactory(CollectActivityFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
