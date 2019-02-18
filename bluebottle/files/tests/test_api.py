import json

from django.core.urlresolvers import reverse
from django.test import TestCase

from bluebottle.files.models import File
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class FileListAPITestCase(TestCase):
    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.url = reverse('file-list')
        self.file_path = './bluebottle/files/tests/files/test-image.png'

        super(FileListAPITestCase, self).setUp()

    def test_create_file(self):
        with open(self.file_path) as test_file:
            response = self.client.post(
                self.url,
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="filename.jpg"',
                HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
            )

        data = json.loads(response.content)

        file = File.objects.get(pk=data['data']['id'])
        self.assertEqual(data['data']['attributes']['token'], unicode(file.token))
