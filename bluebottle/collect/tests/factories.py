from builtins import object

import factory.fuzzy
from pytz import UTC

from bluebottle.test.factory_models.geo import GeolocationFactory

from bluebottle.collect.models import CollectActivity, CollectContributor, CollectType
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class CollectTypeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = CollectType

    disabled = False
    name = factory.Sequence(lambda n: 'CollectType_{0}'.format(n))
    unit = factory.Faker('word')
    unit_plural = factory.Faker('word')


class CollectActivityFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = CollectActivity

    title = factory.Faker('sentence')
    slug = factory.Faker('slug')
    description = factory.Faker('text')

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    collect_type = factory.SubFactory(CollectTypeFactory)
    location = factory.SubFactory(GeolocationFactory)
    start = factory.Faker('future_date', end_date="+20d", tzinfo=UTC)
    end = factory.Faker('future_date', end_date="+2d", tzinfo=UTC)


class CollectContributorFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = CollectContributor

    activity = factory.SubFactory(CollectActivityFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
