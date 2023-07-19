import factory.fuzzy

from bluebottle.updates.models import Update
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class UpdateFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Update

    message = factory.Faker('sentence')
    author = factory.SubFactory(BlueBottleUserFactory)
    activity = factory.SubFactory(DeedFactory)
