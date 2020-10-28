import factory

from bluebottle.statistics.models import Statistic


class StatisticFactory(factory.DjangoModelFactory):
    class Meta:
        model = Statistic

    type = 'manual'
    title = factory.Sequence(lambda n: f'Metric {n}')
    value = None
    sequence = factory.Sequence(lambda n: n)
    active = True
    language = 'en'
