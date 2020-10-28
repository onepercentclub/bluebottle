import factory

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.files.models import Image, Document, PrivateDocument


class ImageFactory(factory.DjangoModelFactory):
    class Meta:
        model = Image

    owner = factory.SubFactory(BlueBottleUserFactory)
    file = factory.django.FileField()


class DocumentFactory(factory.DjangoModelFactory):
    class Meta:
        model = Document

    owner = factory.SubFactory(BlueBottleUserFactory)
    file = factory.django.FileField()


class PrivateDocumentFactory(factory.DjangoModelFactory):
    class Meta:
        model = PrivateDocument

    owner = factory.SubFactory(BlueBottleUserFactory)
    file = factory.django.FileField()
