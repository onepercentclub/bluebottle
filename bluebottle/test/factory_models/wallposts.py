import factory
from django.core.files.uploadedfile import SimpleUploadedFile

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.wallposts.models import (
    TextWallpost, Reaction, SystemWallpost, MediaWallpost, MediaWallpostPhoto)
from .accounts import BlueBottleUserFactory


class TextWallpostFactory(factory.DjangoModelFactory):
    class Meta:
        model = TextWallpost

    content_object = factory.SubFactory(InitiativeFactory)
    author = factory.SubFactory(BlueBottleUserFactory)
    editor = factory.SubFactory(BlueBottleUserFactory)
    ip_address = "127.0.0.1"
    text = factory.Sequence(lambda n: f'Text Wall Post {n}')


class SystemWallpostFactory(factory.DjangoModelFactory):
    class Meta:
        model = SystemWallpost


class ReactionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Reaction


class MediaWallpostFactory(factory.DjangoModelFactory):
    class Meta:
        model = MediaWallpost

    content_object = factory.SubFactory(InitiativeFactory)
    author = factory.SubFactory(BlueBottleUserFactory)
    editor = factory.SubFactory(BlueBottleUserFactory)
    ip_address = "127.0.0.1"
    text = factory.Sequence(lambda n: f'Media Wall Post {n}')


class MediaWallpostPhotoFactory(factory.DjangoModelFactory):
    class Meta:
        model = MediaWallpostPhoto

    mediawallpost = factory.SubFactory(MediaWallpostFactory)
    photo = SimpleUploadedFile(name='test_image.jpg',
                               content=b'',
                               content_type='image/jpeg')
