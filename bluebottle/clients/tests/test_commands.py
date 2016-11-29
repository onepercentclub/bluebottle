import mock

from django.test import TestCase
from django.test.utils import override_settings
from django.core.management import call_command


@override_settings(TENANT_APPS=('django_nose',),
                   TENANT_MODEL='client.clients',
                   DATABASE_ROUTERS=('tenant_schemas.routers.TenantSyncRouter', ))
class ManagementCommandArgsTests(TestCase):
    def test_new_tenant(self):
        from ..management.commands.new_tenant import Command as NewTenantCommand
        cmd = NewTenantCommand()

        self.assertEqual(len(cmd.option_list), 5)
        self.assertEqual(cmd.option_list[0].dest, 'full_name')
        self.assertEqual(cmd.option_list[1].dest, 'schema_name')
        self.assertEqual(cmd.option_list[2].dest, 'domain_url')
        self.assertEqual(cmd.option_list[3].dest, 'client_name')
        self.assertEqual(cmd.option_list[4].dest, 'post_command')


@override_settings(TENANT_APPS=('django_nose',),
                   TENANT_MODEL='client.clients',
                   DATABASE_ROUTERS=('tenant_schemas.routers.TenantSyncRouter',))
class ManagementCommandTests(TestCase):
    def test_new_tenant(self):
        from ..management.commands.new_tenant import Command as NewTenantCommand
        cmd = NewTenantCommand()

        with mock.patch('bluebottle.clients.management.commands.new_tenant.Command.handle') as handle_mock:
            call_command(cmd, full_name='Test Client',
                         schema_name='test_schema',
                         domain_url='test.localhost',
                         client_name='test')
            args, kwargs = handle_mock.call_args_list[0]
            self.assertEqual(kwargs['full_name'], 'Test Client')
            self.assertEqual(kwargs['schema_name'], 'test_schema')
            self.assertEqual(kwargs['client_name'], 'test')
            self.assertEqual(kwargs['domain_url'], 'test.localhost')
