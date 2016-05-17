import factory

from bluebottle.donations.models import Donation
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.fundraisers import FundraiserFactory


class DonationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Donation

    fundraiser = factory.SubFactory(FundraiserFactory)
    order = factory.SubFactory(OrderFactory)
    project = factory.SubFactory(ProjectFactory)
    reward = None
    amount = 25
