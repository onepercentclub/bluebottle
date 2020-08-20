import datetime
from django.db import connection
from django.utils import timezone

from rest_framework import status

from bluebottle.test.utils import BluebottleTestCase

from bluebottle.exports.exporter import Exporter
from bluebottle.exports.tasks import export


class TestExportAdmin(BluebottleTestCase):
    def setUp(self):
        super(TestExportAdmin, self).setUp()

        self.tenant = connection.tenant

    def test_download(self):
        result = export(
            Exporter,
            tenant=self.tenant,
            from_date=timezone.now(),
            to_date=timezone.now() - datetime.timedelta(days=180)
        )

        response = self.client.get(result)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response['Content-Disposition'].startswith(
                'attachment; filename="export-'
            )
        )
        self.assertTrue(
            response['X-Accel-Redirect'].startswith(
                '/media/exports/export'
            )
        )
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_download_invalid_signature(self):
        result = export(
            Exporter,
            tenant=self.tenant,
            from_date=timezone.now(),
            to_date=timezone.now() - datetime.timedelta(days=180)
        )

        response = self.client.get(result + '123')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
