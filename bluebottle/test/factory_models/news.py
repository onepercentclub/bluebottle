import factory
from django.utils.timezone import now

from fluent_contents.models import Placeholder
from bluebottle.news.models import NewsItem
from .accounts import BlueBottleUserFactory


class NewsItemFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = NewsItem

    title = factory.Sequence(lambda n: 'News Title {0}'.format(n))
    status = NewsItem.PostStatus.published
    main_image = factory.django.ImageField(color='blue')
    publication_date = now()
    language = 'nl'
    slug = factory.Sequence(lambda n: 'slug-{0}'.format(n))
    author = factory.SubFactory(BlueBottleUserFactory)

    make_placeholder = factory.PostGeneration(
        lambda obj, create, extracted,
        **kwargs: Placeholder.objects.create_for_object(obj,
                                                        'blog_contents'))


class DraftNewsItemFactory(NewsItemFactory):
    status = NewsItem.PostStatus.draft
