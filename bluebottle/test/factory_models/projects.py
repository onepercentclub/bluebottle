from datetime import timedelta

from djmoney.money import Money

from bluebottle.test.factory_models.utils import LanguageFactory
from django.utils import timezone

import factory

from bluebottle.bb_projects.models import ProjectTheme, ProjectPhase
from bluebottle.projects.models import Project, ProjectLocation

from .accounts import BlueBottleUserFactory
from .geo import CountryFactory
from .organizations import OrganizationFactory


class ProjectThemeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ProjectTheme
        django_get_or_create = ('slug',)

    name = factory.Sequence(lambda n: 'Theme_{0}'.format(n))
    slug = name
    description = 'ProjectTheme factory model'


class ProjectPhaseFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ProjectPhase
        django_get_or_create = ('sequence',)

    name = factory.Sequence(lambda n: 'Phase_{0}'.format(n))
    sequence = factory.Sequence(lambda n: n)


class ProjectLocationFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = ProjectLocation

    latitude = 43.068620
    longitude = 23.676374


class ProjectFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Project

    owner = factory.SubFactory(BlueBottleUserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    title = factory.Sequence(lambda n: 'Project_{0}'.format(n))
    status = factory.SubFactory(ProjectPhaseFactory, sequence=1)
    theme = factory.SubFactory(ProjectThemeFactory, slug='education')
    country = factory.SubFactory(CountryFactory)
    currencies = ['EUR']

    language = factory.SubFactory(LanguageFactory)

    deadline = timezone.now() + timedelta(days=100)
    amount_needed = Money(100, 'EUR')
    amount_asked = Money(100, 'EUR')
    allow_overfunding = True
