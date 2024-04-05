from builtins import object

import factory

from bluebottle.files.tests.factories import ImageFactory
from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.factory_models.projects import ThemeFactory


class InitiativeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Initiative

    title = factory.Faker('sentence')
    story = factory.Faker('text')
    pitch = factory.Faker('text')
    owner = factory.SubFactory(BlueBottleUserFactory)
    # activity_managers = factory.SubFactory(BlueBottleUserFactory)
    has_organization = False

    theme = factory.SubFactory(ThemeFactory)
    image = factory.SubFactory(ImageFactory)
    place = factory.SubFactory(GeolocationFactory)


class InitiativePlatformSettingsFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = InitiativePlatformSettings
