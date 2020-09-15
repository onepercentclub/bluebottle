import factory
from djmoney.contrib.exchange.models import Rate, ExchangeBackend


class ExchangeBackendFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ExchangeBackend

    name = 'openexchange.org'
    base_currency = 'USD'


class RateFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Rate

    backend = factory.SubFactory(ExchangeBackendFactory)
