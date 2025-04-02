from datetime import date, timedelta
from builtins import object

from bluebottle.test.factory_models import generate_rich_text

import factory.fuzzy

from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.activities.models import EffortContribution
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class DeedFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Deed

    title = factory.Faker('sentence')
    slug = factory.Faker('slug')
    description = factory.LazyFunction(generate_rich_text)

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    start = factory.fuzzy.FuzzyDate(
        date.today(),
        date.today() + timedelta(days=2)
    )

    end = factory.fuzzy.FuzzyDate(
        date.today() + timedelta(days=3),
        date.today() + timedelta(days=20)
    )


class DeedParticipantFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = DeedParticipant

    activity = factory.SubFactory(DeedFactory)
    user = factory.SubFactory(BlueBottleUserFactory)


class EffortContributionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = EffortContribution

    contributor = factory.SubFactory(DeedParticipantFactory)
