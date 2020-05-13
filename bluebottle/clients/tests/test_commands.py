import json

import mock
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import override_settings

from bluebottle.clients.management.commands.new_tenant import Command as NewTenantCommand
from bluebottle.clients.models import Client
from bluebottle.members.models import Member


@override_settings(TENANT_APPS=('django_nose',),
                   TENANT_MODEL='clients.Client',
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
        with mock.patch(store_func) as store_mock, mock.patch(super_func) as super_mock:
            call_command(
                cmd,
                full_name='New Tenant',
                schema_name='new',
                domain_url='http://new.localhost:8000',
                client_name='new'
            )
            store_args, store_kwargs = store_mock.call_args_list[0]

            super_args, super_kwargs = super_mock.call_args_list[0]

        self.assertEqual(store_kwargs['name'], 'New Tenant')
        self.assertEqual(store_kwargs['client_name'], 'new')
        self.assertEqual(super_args, ('new',))

    def test_create_superuser(self):
        cmd = NewTenantCommand()
        tenant = 'test'
        cmd.create_client_superuser(tenant)
        connection.set_tenant(Client.objects.get(schema_name='test'))
        user = Member.objects.get(email='admin@example.com')
        self.assertEqual(user.last_name, 'example')

    def test_load_fixtures(self):
        cmd = NewTenantCommand()
        tenant = 'test'
        with mock.patch('bluebottle.clients.management.commands.new_tenant.call_command') as command_mock:
            cmd.load_fixtures(tenant)
            calls = [mock.call('loaddata', 'skills'),
                     mock.call('loaddata', 'redirects'),
                     mock.call('loaddata', 'project_data'),
                     mock.call('loaddata', 'geo_data')]
            command_mock.assert_has_calls(calls)


@override_settings(MERCHANT_ACCOUNTS=[{
    'merchant': 'docdata',
    'currency': 'EUR',
    'merchant_password': 'welcome123',
    'merchant_name': '1procentclub_nw',
}])
class ManagementCommandExportTenantsTests(TestCase):

    def test_export_tenants(self):
        test = Client.objects.get(client_name='test')
        test.client_name = 'onepercent'
        test.save()

        cmd = 'export_tenants'
        file_name = 'tenants.json'
        call_command(cmd, file='tenants.json')
        fp = open(file_name, "r")
        text = json.load(fp)
        # Only onepercent tenant should get 1procentclub_nw merchant account
        self.assertEqual(text[0]['name'], 'test2')
        self.assertEqual(text[0]['accounts'], [])
        self.assertEqual(text[1]['name'], 'onepercent')
        self.assertEqual(text[1]['accounts'], [{u'service_type': u'docdata', u'username': u'1procentclub_nw'}])
