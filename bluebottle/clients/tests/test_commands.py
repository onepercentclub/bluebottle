import json
import mock
from shutil import copyfile

from django.test import TestCase
from django.test.utils import override_settings
from django.core.management import call_command
from django.conf import settings

from bluebottle.clients.models import Client
from bluebottle.members.models import Member
from bluebottle.categories.models import Category
from bluebottle.projects.models import Project
from bluebottle.tasks.models import Task
from bluebottle.rewards.models import Reward
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.wallposts.models import Wallpost
from bluebottle.orders.models import Order


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


@override_settings(TENANT_APPS=('django_nose',),
                   TENANT_MODEL='clients.Client',
                   DATABASE_ROUTERS=('tenant_schemas.routers.TenantSyncRouter',))
class BulkImportTests(TestCase):
    def setUp(self):
        from ..management.commands.bulk_import import Command as BulkImportCommand
        self.cmd = BulkImportCommand()
        super(BulkImportTests, self).setUp()
        CountryFactory.create(alpha2_code='NL')

    def test_bulk_import_args(self):
        json_file = '/tmp/empty.json'
        with open(json_file, 'w') as outfile:
            outfile.write('{}')

        with mock.patch('bluebottle.clients.management.commands.bulk_import.Command.handle') as handle_mock:
            call_command(self.cmd, file=json_file, tenant='test')
            args, kwargs = handle_mock.call_args_list[0]
            self.assertEqual(kwargs['file'], json_file)
            self.assertEqual(kwargs['tenant'], 'test')

    def test_bulk_import(self):
        # setup some test files
        test_file_dir = '{}/bluebottle/clients/tests/files/'.format(settings.PROJECT_ROOT)
        copyfile('{}test-image.png'.format(test_file_dir), '/tmp/test-image.png')
        json_file = '{}bulk_import.json'.format(test_file_dir)

        call_command(self.cmd, file=json_file, tenant='test')
        # users (includes admin user)
        self.assertEqual(Member.objects.count(), 3)
        user = Member.objects.get(email='bryan@brown.com')
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)
        self.assertEqual(user.username, 'bryan')
        self.assertEqual(user.first_name, 'Bryan')
        self.assertEqual(user.last_name, 'Brown')
        self.assertEqual(user.primary_language, 'en')

        # categories
        self.assertEqual(Category.objects.count(), 1)
        category = Category.objects.get(slug='awesome-actors')
        self.assertEqual(category.title, 'Awesome Actors')
        self.assertEqual(category.description,
                         'Awesome Actors from Around the World')

        # projects
        self.assertEqual(Project.objects.count(), 1)
        project = Project.objects.get(slug='f-x3')
        self.assertEqual(project.owner.email, 'bryan@brown.com')
        self.assertEqual(project.amount_asked.amount, 10000000.00)
        self.assertEqual(project.video_url, 'https://www.youtube.com/watch?v=n1ncordnTMc')

        # tasks
        self.assertEqual(Task.objects.count(), 1)
        task = Task.objects.get(project=project)
        self.assertEqual(task.description, 'This movie is not going to be cheap')
        self.assertEqual(task.status, 'realized')

        # rewards
        self.assertEqual(Reward.objects.count(), 1)
        reward = Reward.objects.get(project=project)
        self.assertEqual(reward.title, 'Front row')
        self.assertEqual(reward.limit, 0)
        self.assertEqual(reward.amount.amount, 100000.00)

        # wallposts
        self.assertEqual(Wallpost.objects.count(), 1)
        wallpost = Wallpost.objects.filter(object_id=project.id).all()[0]
        self.assertEqual(wallpost.author, user)
        self.assertEqual(wallpost.text, 'Best movie ever!')

        # orders
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.status, 'success')
        self.assertEqual(order.total.amount, 35.00)
        self.assertEqual(order.user, user)
        self.assertEqual(order.donations.count(), 1)
        self.assertEqual(order.donations.first().project, project)


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
