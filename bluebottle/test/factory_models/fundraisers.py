import factory

from bluebottle.bb_fundraisers.models import Fundraiser

from .accounts import BlueBottleUserFactory
from .geo import CountryFactory
from .projects import ProjectFactory


class FundraiserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Fundraiser

    owner = factory.SubFactory(BlueBottleUserFactory)
    project = factory.SubFactory(ProjectFactory)
    title = factory.Sequence(lambda n: 'Project_{0}'.format(n))
    description = factory.Sequence(lambda n: 'Project_{0}'.format(n))
    amount = 1000
    deadline = factory.fuzzy.FuzzyDateTime(now(), now() + timedelta(weeks=4))
