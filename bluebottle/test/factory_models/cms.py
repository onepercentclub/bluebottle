from datetime import timedelta
import factory

from django.utils.timezone import now

from bluebottle.cms.models import ResultPage, StatsContent, Stats, Stat


class ResultPageFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ResultPage

    title = factory.Sequence(lambda n: 'Result Page Title {0}'.format(n))
    slug = factory.Sequence(lambda n: 'slug-{0}'.format(n))
    description = factory.Sequence(lambda n: 'Results description {0}'.format(n))
    start_date = now() - timedelta(days=300)
    end_date = now() + timedelta(days=65)


class StatsFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Stats

    name = factory.Sequence(lambda n: 'Stats {}'.format(n))


class StatFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Stat

    name = factory.Sequence(lambda n: 'Stat {}'.format(n))
    type = 'manual'
    value = 500
    stats = factory.SubFactory(Stats)
