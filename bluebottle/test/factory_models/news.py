from datetime import timedelta

import factory
from django.utils.timezone import now

from fluent_contents.models import Placeholder
from bluebottle.news.models import NewsItem
from bluebottle.utils.models import PublishedStatus
from .accounts import BlueBottleUserFactory


class NewsItemFactory(factory.DjangoModelFactory):
    class Meta:
        model = NewsItem

    title = factory.Sequence(lambda n: f'News Title {n}')
    status = PublishedStatus.published
    main_image = factory.django.ImageField(color='blue')
    publication_date = now() - timedelta(days=4)
    language = 'nl'
    slug = factory.Sequence(lambda n: f'slug-{n}')
    author = factory.SubFactory(BlueBottleUserFactory)

    make_placeholder = factory.PostGeneration(
        lambda obj, create, extracted,
        **kwargs: Placeholder.objects.create_for_object(obj, 'blog_contents'))
