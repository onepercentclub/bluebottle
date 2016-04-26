from datetime import timedelta

from django.utils import timezone

import factory

from bluebottle.utils.model_dispatcher import get_project_model
from bluebottle.bb_projects.models import ProjectTheme, ProjectPhase

from .accounts import BlueBottleUserFactory
from .geo import CountryFactory
from .organizations import OrganizationFactory

PROJECT_MODEL = get_project_model()


class ProjectThemeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = ProjectTheme
    FACTORY_DJANGO_GET_OR_CREATE = ('name',)

    name = factory.Sequence(lambda n: 'Theme_{0}'.format(n))
    name_nl = name
    slug = name
    description = 'ProjectTheme factory model'


class ProjectPhaseFactory(factory.DjangoModelFactory):
    FACTORY_FOR = ProjectPhase
    FACTORY_DJANGO_GET_OR_CREATE = ('sequence',)

    name = factory.Sequence(lambda n: 'Phase_{0}'.format(n))
    sequence = factory.Sequence(lambda n: n)


class ProjectFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PROJECT_MODEL

    owner = factory.SubFactory(BlueBottleUserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    title = factory.Sequence(lambda n: 'Project_{0}'.format(n))
    status = factory.SubFactory(ProjectPhaseFactory, sequence=1)
    theme = factory.SubFactory(ProjectThemeFactory, name='Education')
    country = factory.SubFactory(CountryFactory)

    deadline = timezone.now() + timedelta(days=100)
    amount_needed = 100
    amount_asked = 100
    allow_overfunding = True

    account_bic = 'ABNANL2A'
    account_number = 'NL18ABNA0484869868'
    account_bank_country = factory.SubFactory(CountryFactory)

    account_holder_name = 'test name'
    account_holder_address = 'test'
    account_holder_postal_code = '1234ab'
    account_holder_city = 'test'
    account_holder_country = factory.SubFactory(CountryFactory)

