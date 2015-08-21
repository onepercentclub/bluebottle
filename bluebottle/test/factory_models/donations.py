import factory
from bluebottle.utils.model_dispatcher import get_model_class
from .orders import OrderFactory
from .projects import ProjectFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.fundraisers import FundraiserFactory

DONATION_MODEL = get_model_class("DONATIONS_DONATION_MODEL")


class DonationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DONATION_MODEL

    fundraiser = factory.SubFactory(FundraiserFactory)
    order = factory.SubFactory(OrderFactory)
    project = factory.SubFactory(ProjectFactory)
    amount = 25
