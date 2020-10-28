import factory.fuzzy

from bluebottle.statistics.models import (
    ManualStatistic, DatabaseStatistic, ImpactStatistic
)


class ManualStatisticFactory(factory.DjangoModelFactory):
    class Meta:
        model = ManualStatistic

    name = factory.Faker('sentence')
    value = 200


class DatabaseStatisticFactory(factory.DjangoModelFactory):
    class Meta:
        model = DatabaseStatistic

    name = factory.Faker('sentence')


class ImpactStatisticFactory(factory.DjangoModelFactory):
    class Meta:
        model = ImpactStatistic
