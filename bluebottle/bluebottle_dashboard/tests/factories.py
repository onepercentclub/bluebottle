import factory.fuzzy
from jet.dashboard.models import UserDashboardModule

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class UserDashboardModuleFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = UserDashboardModule

    title = factory.Faker('sentence')
    user = factory.SubFactory(BlueBottleUserFactory)
    column = 1
    order = 1
