from datetime import timedelta

import factory
from django.utils.timezone import now

from bluebottle.pages.models import Page
from .accounts import BlueBottleUserFactory


class PageFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Page

    language = 'en'
    title = factory.Sequence(lambda n: 'Page Title {0}'.format(n))
    author = factory.SubFactory(BlueBottleUserFactory)
    slug = factory.Sequence(lambda n: 'slug-{0}'.format(n))
    status = Page.PageStatus.published
    publication_date = now() - timedelta(days=4)
