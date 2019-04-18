import json

from django.core.urlresolvers import reverse
from django.test import TestCase

from bluebottle.files.models import Image
from bluebottle.test.utils import JSONAPITestClient
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class FileListAPITestCase(TestCase):
    def setUp(self):
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory.create()
        self.url = reverse('image-list')
        self.file_path = './bluebottle/files/tests/files/test-image.png'

        super(FileListAPITestCase, self).setUp()

    def test_create_file(self):
        with open(self.file_path) as test_file:
            response = self.client.post(
                self.url,
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="filename.png"',
                user=self.owner
            )

        data = json.loads(response.content)

        file_field = Image.objects.get(pk=data['data']['id'])

        self.assertEqual(data['data']['type'], 'images')
        self.assertEqual(data['data']['relationships']['owner']['data']['id'], unicode(self.owner.pk))
        self.assertTrue(file_field.file.name.endswith(data['data']['meta']['filename']))
        self.assertEqual(data['data']['meta']['size'], 1145)

    def test_create_file_anonymous(self):
        with open(self.file_path) as test_file:
            response = self.client.post(
                self.url,
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="filename.png"',
            )

        self.assertEqual(response.status_code, 401)

    def test_create_file_spoofed_mime_type(self):
        with open(self.file_path) as test_file:
            response = self.client.post(
                self.url,
                test_file.read(),
                content_type="text/html",
                HTTP_CONTENT_DISPOSITION='attachment; filename="filename.png"',
                user=self.owner
            )

        self.assertEqual(response.status_code, 400)
