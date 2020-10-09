from builtins import object
import factory
from django.core.files.uploadedfile import SimpleUploadedFile

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.wallposts.models import (
    TextWallpost, Reaction, SystemWallpost, MediaWallpost, MediaWallpostPhoto)
from .accounts import BlueBottleUserFactory


class TextWallpostFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = TextWallpost

    content_object = factory.SubFactory(InitiativeFactory)
    author = factory.SubFactory(BlueBottleUserFactory)
    editor = factory.SubFactory(BlueBottleUserFactory)
    ip_address = "127.0.0.1"
    text = factory.Sequence(lambda n: 'Text Wall Post {0}'.format(n))


class SystemWallpostFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = SystemWallpost


class ReactionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Reaction


class MediaWallpostFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = MediaWallpost

    content_object = factory.SubFactory(InitiativeFactory)
    author = factory.SubFactory(BlueBottleUserFactory)
    editor = factory.SubFactory(BlueBottleUserFactory)
    ip_address = "127.0.0.1"
    text = factory.Sequence(lambda n: 'Media Wall Post {0}'.format(n))


class MediaWallpostPhotoFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = MediaWallpostPhoto

    mediawallpost = factory.SubFactory(MediaWallpostFactory)
    photo = SimpleUploadedFile(name='test_image.jpg',
                               content=b'',
                               content_type='image/jpeg')
