import factory
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from fluent_contents.models import Placeholder
from bluebottle.pages.models import Page
from .accounts import BlueBottleUserFactory

class PageFactory(factory.DjangoModelFactory):
	FACTORY_FOR = Page

	language = 'en'
	title = factory.Sequence(lambda n: 'Page Title {0}'.format(n))
	author = factory.SubFactory(BlueBottleUserFactory)
	status = Page.PageStatus.published
	publication_date = now()
