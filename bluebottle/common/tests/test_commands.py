from django.test import TestCase
from django.test.utils import override_settings
from ..management.commands.base import Command


@override_settings(TENANT_APPS=('django_nose',),
                   TENANT_MODEL='client.clients',
                   DATABASE_ROUTERS=('tenant_schemas.routers.TenantSyncRouter',))
class ManagementCommandArgsTests(TestCase):
    def test_base(self):
        cmd = Command()

        self.assertEqual(cmd.option_list, [])
