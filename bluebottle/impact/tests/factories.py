from builtins import object
import factory.fuzzy

from bluebottle.impact.models import ImpactType, ImpactGoal
from bluebottle.events.tests.factories import EventFactory


class ImpactTypeFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = ImpactType

    name = factory.Faker('sentence')
    text = factory.Faker('sentence')

    text_with_target = factory.fuzzy.FuzzyChoice(
        ['reach {} people', 'save {} kg CO2', 'administer {} vaccinations']
    )

    text_passed = factory.fuzzy.FuzzyChoice(
        ['people reached', 'kg CO2 saved', 'vaccinations administered']
    )


class ImpactGoalFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ImpactGoal

    target = factory.fuzzy.FuzzyInteger(10, 20)
    realized = factory.fuzzy.FuzzyInteger(0, 15)

    type = factory.SubFactory(ImpactTypeFactory)
    activity = factory.SubFactory(EventFactory, status='succeeded')
