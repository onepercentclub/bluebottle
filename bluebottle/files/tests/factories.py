import factory

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.files.models import Image, Document


class ImageFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Image

    owner = factory.SubFactory(BlueBottleUserFactory)
    file = factory.django.FileField()


class DocumentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Document

    owner = factory.SubFactory(BlueBottleUserFactory)
    file = factory.django.FileField()
