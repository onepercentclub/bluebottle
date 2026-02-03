from builtins import object
from datetime import timedelta

import factory.fuzzy
from django.utils.timezone import now
from moneyed import Money

from bluebottle.activity_links.models import LinkedDeed, LinkedFunding
from bluebottle.test.factory_models import generate_rich_text


class LinkedDeedFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = LinkedDeed

    title = factory.Faker('sentence')
    description = factory.LazyFunction(generate_rich_text)
    status = 'open'

    start = factory.fuzzy.FuzzyDateTime(
        now(),
        now() + timedelta(days=2)
    )

    end = factory.fuzzy.FuzzyDateTime(
        now() + timedelta(days=3),
        now() + timedelta(days=20)
    )


class LinkedFundingFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = LinkedFunding

    status = 'open'

    title = factory.Faker('sentence')
    description = factory.LazyFunction(generate_rich_text)

    target = Money(5000, 'EUR')
    donated = Money(1000, 'EUR')
