import json

from django.core.urlresolvers import reverse
from django.test import TestCase

from bluebottle.files.models import Image, Document
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import JSONAPITestClient


class FileListAPITestCase(TestCase):
    def setUp(self):
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory.create()
        self.image_url = reverse('image-list')
        self.document_url = reverse('document-list')
        self.image_path = './bluebottle/files/tests/files/test-image.png'
        self.document_path = './bluebottle/files/tests/files/test.rtf'

        super(FileListAPITestCase, self).setUp()

    def test_create_document(self):
        with open(self.document_path) as test_file:
            response = self.client.post(
                self.document_url,
                test_file.read(),
                content_type="text/rtf",
                HTTP_CONTENT_DISPOSITION='attachment; filename="test.rtf"',
                user=self.owner
            )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['data']['type'], 'documents')
        self.assertEqual(data['data']['relationships']['owner']['data']['id'], unicode(self.owner.pk))
        self.assertEqual(data['data']['meta']['size'], 39109)

        file_field = Document.objects.get(pk=data['data']['id'])
        self.assertTrue(file_field.file.name.endswith(data['data']['meta']['filename']))

    def test_create_image(self):
        with open(self.image_path) as test_file:
            response = self.client.post(
                self.image_url,
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="filename.png"',
                user=self.owner
            )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)

        file_field = Image.objects.get(pk=data['data']['id'])

        self.assertEqual(data['data']['type'], 'images')
        self.assertEqual(data['data']['relationships']['owner']['data']['id'], unicode(self.owner.pk))
        self.assertTrue(file_field.file.name.endswith(data['data']['meta']['filename']))
        self.assertEqual(data['data']['meta']['size'], 1145)

    def test_create_image_anonymous(self):
        with open(self.image_path) as test_file:
            response = self.client.post(
                self.image_url,
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="filename.png"',
            )

        self.assertEqual(response.status_code, 401)

    def test_create_image_spoofed_mime_type(self):
        with open(self.image_path) as test_file:
            response = self.client.post(
                self.image_url,
                test_file.read(),
                content_type="text/html",
                HTTP_CONTENT_DISPOSITION='attachment; filename="filename.png"',
                user=self.owner
            )

        self.assertEqual(response.status_code, 400)
