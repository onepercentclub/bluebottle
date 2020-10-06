import mock
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import override_settings

from bluebottle.clients.management.commands.new_tenant import Command as NewTenantCommand
from bluebottle.clients.models import Client


@override_settings(TENANT_APPS=('django_nose',),
                   TENANT_MODEL='clients.Client',
                   DATABASE_ROUTERS=('tenant_schemas.routers.TenantSyncRouter', ))
class ManagementCommandArgsTests(TestCase):
    def test_new_tenant(self):
        from ..management.commands.new_tenant import Command as NewTenantCommand
        cmd = NewTenantCommand()

        self.assertEqual(len(cmd.option_list), 6)
        self.assertEqual(cmd.option_list[0].dest, 'full_name')
        self.assertEqual(cmd.option_list[1].dest, 'schema_name')
        self.assertEqual(cmd.option_list[2].dest, 'domain_url')
        self.assertEqual(cmd.option_list[3].dest, 'client_name')
        self.assertEqual(cmd.option_list[4].dest, 'languages')
        self.assertEqual(cmd.option_list[5].dest, 'post_command')


@override_settings(TENANT_APPS=('django_nose',),
                   TENANT_MODEL='clients.Client',
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


class ManagementCommandNewTenantTests(TestCase):
    def test_create_new_tenant(self):
        connection.set_schema_to_public()
        cmd = NewTenantCommand()
        store_func = 'bluebottle.clients.management.commands.new_tenant.Command.store_client'
        super_func = 'bluebottle.clients.management.commands.new_tenant.Command.create_client_superuser'
        language_func = 'bluebottle.clients.management.commands.new_tenant.Command.create_languages'
        command_func = 'bluebottle.clients.management.commands.new_tenant.call_command'
        tenant = Client(name='New Tenant', schema_name='new', client_name='new')
        with mock.patch(store_func, return_value=tenant) as store_mock, \
                mock.patch(super_func) as super_mock, \
                mock.patch(command_func) as command_mock, \
                mock.patch(language_func) as language_mock:
            call_command(
                cmd,
                full_name='New Tenant',
                schema_name='new',
                domain_url='http://new.localhost:8000',
                client_name='new'
            )
            store_args, store_kwargs = store_mock.call_args_list[0]
            super_args, super_kwargs = super_mock.call_args_list[0]
            command_args, command_kwargs = command_mock.call_args_list[0]
            language_args, language_kwargs = language_mock.call_args_list[0]

        self.assertEqual(store_kwargs['name'], 'New Tenant')
        self.assertEqual(store_kwargs['client_name'], 'new')
        self.assertEqual(super_args, ())
        self.assertEqual(language_args, ('en',))
        self.assertEqual(command_args, ('loaddata', 'geo_data'))
