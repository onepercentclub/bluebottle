import factory
import logging

from django.conf import settings

from bluebottle.projects.models import (
    Project, ProjectTheme, ProjectDetailField, ProjectBudgetLine)
from .accounts import BlueBottleUserFactory

# Suppress debug information for Factory Boy
logging.getLogger('factory').setLevel(logging.WARN)


class ProjectFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Project

    owner = factory.SubFactory(BlueBottleUserFactory)
    phase = settings.PROJECT_PHASES[0][1][0][0]
    title = factory.Sequence(lambda n: 'Project_{0}'.format(n))


class ProjectThemeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = ProjectTheme

    name = factory.Sequence(lambda n: 'Theme_{0}'.format(n))
    name_nl = name
    slug = name
    description = 'ProjectTheme factory model'


class ProjectDetailFieldFactory(factory.DjangoModelFactory):
    FACTORY_FOR = ProjectDetailField

    name = factory.Sequence(lambda n: 'Field_{0}'.format(n))
    description = 'DetailField factory model'
    slug = name
    type = 'text'


class ProjectBudgetLineFactory(factory.DjangoModelFactory):
    FACTORY_FOR = ProjectBudgetLine

    project = factory.SubFactory(ProjectFactory)
    amount = 100000
