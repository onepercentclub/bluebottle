import factory

from bluebottle.utils.utils import get_project_model

from .accounts import BlueBottleUserFactory
from .geo import CountryFactory

PROJECT_MODEL = get_project_model()


class ProjectThemeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = ProjectTheme
    FACTORY_DJANGO_GET_OR_CREATE = ('name', )

    name = factory.Sequence(lambda n: 'Theme_{0}'.format(n))
    name_nl = name
    slug = name
    description = 'ProjectTheme factory model'


class ProjectPhaseFactory(factory.DjangoModelFactory):
    FACTORY_FOR = ProjectPhase
    FACTORY_DJANGO_GET_OR_CREATE = ('name',)

    name = factory.Sequence(lambda n: 'Phase_{0}'.format(n))
    sequence = factory.Sequence(lambda n: n)


class ProjectFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PROJECT_MODEL

    owner = factory.SubFactory(BlueBottleUserFactory)
    title = factory.Sequence(lambda n: 'Project_{0}'.format(n))
    status = factory.SubFactory(ProjectPhaseFactory)
    theme = factory.SubFactory(ProjectThemeFactory)
    country = factory.SubFactory(CountryFactory)
