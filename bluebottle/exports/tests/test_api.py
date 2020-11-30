import datetime
from django.db import connection
from django.utils import timezone

from rest_framework import status

from bluebottle.test.utils import BluebottleAdminTestCase
from django.urls.base import reverse

from bluebottle.exports.exporter import Exporter
from bluebottle.exports.tasks import export


class TestExportAdmin(BluebottleAdminTestCase):
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

        self.client.force_login(self.superuser)
        response = self.client.get(reverse('exportdb_download', args=(result, )))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response['Content-Disposition'].startswith(
                'attachment; filename="export-'
            )
        )
        self.assertTrue(
            response['X-Accel-Redirect'].startswith(
                '/media/private/exports/export'
            )
        )
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_download_not_logged_in(self):
        result = export(
            Exporter,
            tenant=self.tenant,
            from_date=timezone.now(),
            to_date=timezone.now() - datetime.timedelta(days=180)
        )

        response = self.client.get(reverse('exportdb_download', args=(result, )))

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue(response['location'].startswith('/en/admin/login/?next=/en/admin/exportdb'))
