from builtins import str

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from bluebottle.files.tests.factories import ImageFactory
from bluebottle.files.models import Image
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class ImageTestCase(TestCase):

    def test_file_properties(self):
        image = ImageFactory.create()
        self.assertEqual(str(image), str(image.id))
        self.assertGreater(len(str(image)), 8)

    def test_default_cropbox_wide_image(self):
        path = './bluebottle/files/tests/files/image-wide.png'
        with open(path, 'rb') as file:
            file = SimpleUploadedFile(
                name="image-wide.png",
                content=file.read(),
                content_type="image/png"
            )
            image = Image(file=file, owner=BlueBottleUserFactory.create())

        image.save()

        self.assertEqual(image.cropbox, "62,40,337,160")

    def test_default_cropbox_narrow_image(self):
        path = './bluebottle/files/tests/files/image-narrow.png'
        with open(path, 'rb') as file:
            file = SimpleUploadedFile(
                name="image-narrow.png",
                content=file.read(),
                content_type="image/png"
            )
            image = Image(file=file, owner=BlueBottleUserFactory.create())

        image.save()

        self.assertEqual(image.cropbox, "40,133,160,166")
