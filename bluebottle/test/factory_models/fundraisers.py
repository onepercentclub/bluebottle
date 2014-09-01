from datetime import timedelta
from django.utils.timezone import now
import factory

from bluebottle.fundraisers.models import FundRaiser

from .accounts import BlueBottleUserFactory
from .projects import ProjectFactory


class FundraiserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = FundRaiser

    owner = factory.SubFactory(BlueBottleUserFactory)
    project = factory.SubFactory(ProjectFactory)
    title = factory.Sequence(lambda n: 'Project_{0}'.format(n))
    description = factory.Sequence(lambda n: 'Project_{0}'.format(n))
    amount = 1000
    deadline = factory.fuzzy.FuzzyDateTime(now(), now() + timedelta(weeks=4))
