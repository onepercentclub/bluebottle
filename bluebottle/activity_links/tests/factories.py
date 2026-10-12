from builtins import object
from datetime import timedelta

import factory.fuzzy
from django.utils.timezone import now
from moneyed import Money

from bluebottle.activity_links.models import (
    LinkedDateActivity,
    LinkedDateSlot,
    LinkedDeadlineActivity,
    LinkedDeed,
    LinkedFunding,
    LinkedGrantApplication,
)
from bluebottle.test.factory_models import generate_rich_text
from bluebottle.test.factory_models.geo import GeolocationFactory


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


class LinkedGrantApplicationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = LinkedGrantApplication

    status = 'open'

    title = factory.Faker('sentence')
    description = factory.LazyFunction(generate_rich_text)

    target = Money(2500, 'EUR')


class LinkedDateActivityFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = LinkedDateActivity

    title = factory.Faker('sentence')
    description = factory.LazyFunction(generate_rich_text)
    status = 'open'


class LinkedDateSlotFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = LinkedDateSlot

    activity = factory.SubFactory(LinkedDateActivityFactory)
    start = now() + timedelta(weeks=4)
    end = now() + timedelta(weeks=4, hours=2)
    location = factory.SubFactory(GeolocationFactory, with_geofeatures=True)


class LinkedDeadlineActivityFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = LinkedDeadlineActivity

    title = factory.Faker('sentence')
    description = factory.LazyFunction(generate_rich_text)
    status = 'open'
    start = now() + timedelta(weeks=1)
    end = now() + timedelta(weeks=4)
    duration = timedelta(hours=2)
    location = factory.SubFactory(GeolocationFactory, with_geofeatures=True)
