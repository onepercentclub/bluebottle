import factory

from bluebottle.initiatives.models import Initiative

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectThemeFactory


class InitiativeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Initiative

    review_status = Initiative.ReviewStatus.created
    title = factory.Sequence(lambda n: 'Initiative {0}'.format(n))
    owner = factory.SubFactory(BlueBottleUserFactory)
    reviewer = factory.SubFactory(BlueBottleUserFactory)
    theme = factory.SubFactory(ProjectThemeFactory)
