import factory
from django.utils.timezone import now
from bluebottle.quotes.models import Quote

from .accounts import BlueBottleUserFactory


class QuoteFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Quote

    author = factory.SubFactory(BlueBottleUserFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
    status = Quote.QuoteStatus.published
    publication_date = now()
    quote = factory.Sequence(lambda n: 'Quote {0}'.format(n))
