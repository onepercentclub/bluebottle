import factory
from djmoney.contrib.exchange.models import Rate, ExchangeBackend


class ExchangeBackendFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExchangeBackend

    name = 'openexchangerates.org'
    base_currency = 'USD'


class RateFactory(factory.DjangoModelFactory):
    class Meta:
        model = Rate

    backend = factory.SubFactory(ExchangeBackendFactory)
