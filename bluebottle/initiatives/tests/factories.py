import factory

from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectThemeFactory
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.files.tests.factories import ImageFactory


class InitiativeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Initiative

    status = 'draft'
    title = factory.Faker('sentence')
    story = factory.Faker('text')
    pitch = factory.Faker('text')
    owner = factory.SubFactory(BlueBottleUserFactory)
    reviewer = factory.SubFactory(BlueBottleUserFactory)
    activity_manager = factory.SubFactory(BlueBottleUserFactory)
    has_organization = False

    theme = factory.SubFactory(ProjectThemeFactory)
    image = factory.SubFactory(ImageFactory)
    place = factory.SubFactory(GeolocationFactory)


class InitiativePlatformSettingsFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = InitiativePlatformSettings
