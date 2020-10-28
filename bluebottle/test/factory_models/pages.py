from datetime import timedelta

import factory
from django.utils.timezone import now

from bluebottle.pages.models import Page
from .accounts import BlueBottleUserFactory


class PageFactory(factory.DjangoModelFactory):
    class Meta:
        model = Page

    language = 'en'
    title = factory.Sequence(lambda n: f'Page Title {n}')
    author = factory.SubFactory(BlueBottleUserFactory)
    slug = factory.Sequence(lambda n: f'slug-{n}')
    status = Page.PageStatus.published
    publication_date = now() - timedelta(days=4)
