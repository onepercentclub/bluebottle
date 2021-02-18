from builtins import object

import factory.fuzzy
from pytz import UTC

from bluebottle.deeds.models import Deed
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class DeedFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Deed

    title = factory.Faker('sentence')
    slug = factory.Faker('slug')
    description = factory.Faker('text')

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    end = factory.Faker('future_datetime', tzinfo=UTC)
