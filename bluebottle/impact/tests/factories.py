import factory.fuzzy

from bluebottle.impact.models import ImpactType, ImpactGoal
from bluebottle.events.tests.factories import EventFactory


class ImpactTypeFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = ImpactType

    name = factory.Faker('sentence')
    unit = factory.fuzzy.FuzzyChoice(['people', 'kg CO2', 'vaccinations'])


class ImpactGoalFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ImpactGoal

    target = factory.fuzzy.FuzzyInteger(10, 20)
    realized = factory.fuzzy.FuzzyInteger(0, 15)

    tyoe = factory.SubFactory(ImpactTypeFactory)
    activity = factory.SubFactory(EventFactory)
