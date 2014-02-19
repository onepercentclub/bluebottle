import factory
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from fluent_contents.models import Placeholder
from bluebottle.utils.tests import generate_random_slug
from bluebottle.news.models import NewsItem
from .accounts import BlueBottleUserFactory

class NewsItemFactory(factory.DjangoModelFactory):
	FACTORY_FOR = NewsItem

	title = factory.Sequence(lambda n: 'News Title {0}'.format(n))
	status = NewsItem.PostStatus.published
	publication_date = now()
	language = 'nl'
	slug = generate_random_slug()
	author = factory.SubFactory(BlueBottleUserFactory)

	make_placeholder = factory.PostGeneration(
    	lambda obj, create, extracted, **kwargs: Placeholder.objects.create_for_object(obj, 'blog_contents'))

class DraftNewsItemFactory(NewsItemFactory):

	status = NewsItem.PostStatus.draft