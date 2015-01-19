import datetime
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now

import factory

from bluebottle.utils.model_dispatcher import get_project_model
from bluebottle.bb_projects.models import ProjectTheme, ProjectPhase
from bluebottle.projects.models import PartnerOrganization

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

    deadline = timezone.now() + timedelta(days=100)
    amount_needed = 100
    amount_asked = 100
    allow_overfunding = True


class PartnerFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PartnerOrganization

    FACTORY_DJANGO_GET_OR_CREATE = ('slug',)

    name = factory.Sequence(lambda n: 'Partner_{0}'.format(n))
    slug = factory.Sequence(lambda n: 'partner-{0}'.format(n))
    description = 'Partner Organization factory model'
