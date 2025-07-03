import factory.fuzzy
from builtins import object
from moneyed import Money

from bluebottle.funding.models import (
    GrantApplication
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models import generate_rich_text
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ThemeFactory


class GrantApplicationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = GrantApplication

    title = factory.Faker('sentence')
    slug = factory.Faker('slug')
    description = factory.LazyFunction(generate_rich_text)

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    target = Money(5000, 'EUR')
    theme = factory.SubFactory(ThemeFactory)
