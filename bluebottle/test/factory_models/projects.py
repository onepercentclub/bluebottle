from datetime import timedelta

from bluebottle.test.factory_models.utils import LanguageFactory
from django.utils import timezone

import factory

from bluebottle.bb_projects.models import ProjectTheme, ProjectPhase
from bluebottle.projects.models import Project, ProjectDocument, ProjectLocation

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
    amount_needed = 100
    amount_asked = 100
    allow_overfunding = True

    account_details = 'ABNANL2AABNANL2AABNANL2A'
    account_number = 'NL18ABNA0484869868'
    account_bank_country = factory.SubFactory(CountryFactory)

    account_holder_name = 'test name'
    account_holder_address = 'test'
    account_holder_postal_code = '1234ab'
    account_holder_city = 'test'
    account_holder_country = factory.SubFactory(CountryFactory)


class ProjectDocumentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ProjectDocument

    author = factory.SubFactory(BlueBottleUserFactory)
    project = factory.SubFactory(ProjectFactory)
