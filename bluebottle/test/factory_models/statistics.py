import factory

from bluebottle.statistics.models import Statistic


class StatisticFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Statistic

    type = 'manual'
    title = factory.Sequence(lambda n: 'Metric {0}'.format(n))
    value = None
    sequence = factory.Sequence(lambda n: n)
    active = True
    language = 'en'
