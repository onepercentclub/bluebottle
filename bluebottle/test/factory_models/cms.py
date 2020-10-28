from datetime import timedelta
import factory

from django.utils.timezone import now

from bluebottle.cms.models import (
    ResultPage, HomePage, Stat, Quote,
    SiteLinks, LinkGroup, Link, LinkPermission,
    Step, ContentLink, Greeting
)
from bluebottle.slides.models import Slide
from bluebottle.test.factory_models.utils import LanguageFactory


class ResultPageFactory(factory.DjangoModelFactory):
    class Meta:
        model = ResultPage

    title = factory.Sequence(lambda n: f'Result Page Title {n}')
    slug = factory.Sequence(lambda n: f'slug-{n}')
    description = factory.Sequence(lambda n: f'Results description {n}')
    start_date = now() - timedelta(days=300)
    end_date = now() + timedelta(days=65)


class HomePageFactory(factory.DjangoModelFactory):
    class Meta:
        model = HomePage


class StatFactory(factory.DjangoModelFactory):
    class Meta:
        model = Stat

    type = 'manual'
    value = 500


class QuoteFactory(factory.DjangoModelFactory):
    class Meta:
        model = Quote

    name = factory.Sequence(lambda n: f'Name {n}')
    quote = factory.Sequence(lambda n: f'Quote {n}')


class ContentLinkFactory(factory.DjangoModelFactory):
    class Meta:
        model = ContentLink


class SlideFactory(factory.DjangoModelFactory):
    class Meta:
        model = Slide


class StepFactory(factory.DjangoModelFactory):
    class Meta:
        model = Step


class GreetingFactory(factory.DjangoModelFactory):
    class Meta:
        model = Greeting


class SiteLinksFactory(factory.DjangoModelFactory):
    class Meta:
        model = SiteLinks

    language = factory.SubFactory(LanguageFactory)


class LinkGroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = LinkGroup
        django_get_or_create = ('name',)

    site_links = factory.SubFactory(SiteLinksFactory)
    name = factory.Sequence(lambda n: f'Link Group {n}')


class LinkFactory(factory.DjangoModelFactory):
    class Meta:
        model = Link

    link_group = factory.SubFactory(LinkGroupFactory)
    title = factory.Sequence(lambda n: f'Title {n}')


class LinkPermissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = LinkPermission
