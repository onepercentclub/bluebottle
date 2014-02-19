import factory
from django.contrib.auth import get_user_model

from .accounts import BlueBottleUserFactory
from .projects import ProjectFactory

class TextWallPostFactory(factory.DjangoModelFactory):
	FACTORY_FOR = TextWallPost

	content_object = factory.SubFactory(ProjectFactory)
	owner = factory.SubFactory(BlueBottleUserFactory)
	editor = factory.SubFactory(BlueBottleUserFactory)
	deleted = False
	ip_address = "127.0.0.1"
	text = factory.Sequence(lambda n: 'Text Wall Post {0}'.format(n))