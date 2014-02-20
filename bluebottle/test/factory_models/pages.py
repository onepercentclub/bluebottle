import factory
from django.utils.timezone import now

from bluebottle.pages.models import Page
from .accounts import BlueBottleUserFactory

class PageFactory(factory.DjangoModelFactory):
	FACTORY_FOR = Page

	language = 'en'
	title = factory.Sequence(lambda n: 'Page Title {0}'.format(n))
	author = factory.SubFactory(BlueBottleUserFactory)
	status = Page.PageStatus.published
	publication_date = now()
