import factory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.utils.model_dispatcher import get_donation_model

DONATION_MODEL = get_donation_model()


class DonationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DONATION_MODEL

    amount = 25
    order = factory.SubFactory(OrderFactory)
    project = factory.SubFactory(ProjectFactory)
