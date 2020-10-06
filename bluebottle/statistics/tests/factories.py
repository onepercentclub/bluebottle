from builtins import object
import factory.fuzzy

from bluebottle.statistics.models import (
    ManualStatistic, DatabaseStatistic, ImpactStatistic
)


class ManualStatisticFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ManualStatistic

    name = factory.Faker('sentence')
    value = 200


class DatabaseStatisticFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = DatabaseStatistic

    name = factory.Faker('sentence')


class ImpactStatisticFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ImpactStatistic
