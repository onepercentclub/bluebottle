import factory
from djmoney_rates.models import RateSource, Rate


class RateSourceFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = RateSource

    name = 'openexchange.org'
    base_currency = 'USD'


class RateFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Rate

    source = factory.SubFactory(RateSourceFactory)
