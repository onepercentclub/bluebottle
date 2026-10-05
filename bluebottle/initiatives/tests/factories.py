from builtins import object

import factory

from bluebottle.files.tests.factories import ImageFactory
from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings
from bluebottle.test.factory_models import generate_rich_text
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import GeolocationFactory, CountryFactory
from bluebottle.test.factory_models.projects import ThemeFactory


class InitiativeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Initiative

    title = factory.Faker('sentence')
    story = factory.LazyFunction(generate_rich_text)
    pitch = factory.Faker('text')
    owner = factory.SubFactory(BlueBottleUserFactory)
    has_organization = False

    theme = factory.SubFactory(ThemeFactory)
    image = factory.SubFactory(ImageFactory)
    place = factory.SubFactory(
        GeolocationFactory,
        with_geofeatures=True,
        country=factory.SubFactory(
            CountryFactory,
            # Fix this to Uzbekistan, so we don't get accidental matches when this is set to NL by random
            alpha2_code='UZ',
            name='Uzbekistan'
        )
    )

    @factory.post_generation
    def activity_managers(self, create, extracted, **kwargs):
        if extracted == []:
            return

        if not extracted:
            extracted = [BlueBottleUserFactory.create()]

        for manager in extracted:
            self.activity_managers.add(manager)


class InitiativePlatformSettingsFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = InitiativePlatformSettings
