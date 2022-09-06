import factory.fuzzy

from bluebottle.time_based.tests.factories import PeriodActivityFactory
from bluebottle.activities.models import Team
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class TeamFactory(factory.DjangoModelFactory):
    class Meta:
        model = Team

    owner = factory.SubFactory(BlueBottleUserFactory)
    activity = factory.SubFactory(PeriodActivityFactory)
