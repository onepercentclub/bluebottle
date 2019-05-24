import factory

from bluebottle.initiatives.models import Initiative

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectThemeFactory
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.files.tests.factories import ImageFactory


class InitiativeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Initiative

    status = Initiative.ReviewStatus.created
    title = factory.Faker('sentence')
    story = factory.Faker('text')
    pitch = factory.Faker('text')
    owner = factory.SubFactory(BlueBottleUserFactory)
    reviewer = factory.SubFactory(BlueBottleUserFactory)

    theme = factory.SubFactory(ProjectThemeFactory)
    image = factory.SubFactory(ImageFactory)
    place = factory.SubFactory(GeolocationFactory)
