import factory
from bluebottle.utils.model_dispatcher import get_model_class
from .orders import OrderFactory
from .projects import ProjectFactory


DONATION_MODEL = get_model_class("DONATIONS_DONATION_MODEL")


class DonationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DONATION_MODEL

    order = factory.SubFactory(OrderFactory)
    project = factory.SubFactory(ProjectFactory)