from builtins import object
import factory

from bluebottle.test.factory_models import generate_rich_text

from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ThemeFactory
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.files.tests.factories import ImageFactory


class InitiativeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Initiative

    title = factory.Faker('sentence')
    story = factory.LazyFunction(generate_rich_text)
    pitch = factory.Faker('text')
    owner = factory.SubFactory(BlueBottleUserFactory)
    activity_managers = factory.SubFactory(BlueBottleUserFactory)
    has_organization = False

    theme = factory.SubFactory(ThemeFactory)
    image = factory.SubFactory(ImageFactory)
    place = factory.SubFactory(GeolocationFactory)

    @factory.post_generation
    def activity_managers(self, create, extracted, **kwargs):
        if extracted == []:
            return

        if not extracted:
            extracted = [BlueBottleUserFactory.create()]

        self.activity_managers.clear()
        for manager in extracted:
            self.activity_managers.add(manager)


class InitiativePlatformSettingsFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = InitiativePlatformSettings
