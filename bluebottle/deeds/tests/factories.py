from builtins import object

import factory.fuzzy
from pytz import UTC

from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.activities.models import EffortContribution
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class DeedFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Deed

    title = factory.Faker('sentence')
    slug = factory.Faker('slug')
    description = factory.Faker('text')

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    end = factory.Faker('future_date', end_date="+20d", tzinfo=UTC)
    start = factory.Faker('future_date', end_date="+2d", tzinfo=UTC)


class DeedParticipantFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = DeedParticipant

    activity = factory.SubFactory(DeedFactory)
    user = factory.SubFactory(BlueBottleUserFactory)


class EffortContributionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = EffortContribution

    contributor = factory.SubFactory(DeedParticipantFactory)
