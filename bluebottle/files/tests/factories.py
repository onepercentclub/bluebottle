import factory

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.files.models import Image


class ImageFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Image

    owner = factory.SubFactory(BlueBottleUserFactory)
    file = factory.django.FileField()
