from django.test import TestCase

from bluebottle.files.tests.factories import ImageFactory


class FileTestCase(TestCase):

    def test_file_properties(self):
        image = ImageFactory.create()
        self.assertEqual(str(image), str(image.id))
        self.assertGreater(len(str(image)), 8)
