import mock

from django.test import TestCase
from django.test.utils import override_settings
from django.core.management import call_command
from ..management.commands.base import Command


@override_settings(TENANT_APPS=('django_nose',),
                   TENANT_MODEL='client.clients',
                   DATABASE_ROUTERS=('tenant_schemas.routers.TenantSyncRouter',))
class ManagementCommandArgsTests(TestCase):
    def test_base(self):
        cmd = Command()

        self.assertEqual(cmd.option_list, [])

    def test_txpull(self):
        from ..management.commands.txpull import Command as TxPullCommand
        cmd = TxPullCommand()

        self.assertEqual(len(cmd.option_list), 5)
        self.assertEqual(cmd.option_list[0].dest, 'all')
        self.assertEqual(cmd.option_list[1].dest, 'tenant')
        self.assertEqual(cmd.option_list[2].dest, 'deploy')
        self.assertEqual(cmd.option_list[3].dest, 'frontend')
        self.assertEqual(cmd.option_list[4].dest, 'frontend_dir')

    def test_translate(self):
        from ..management.commands.translate import Command as TranslateCommand
        cmd = TranslateCommand()

        self.assertEqual(len(cmd.option_list), 4)
        self.assertEqual(cmd.option_list[0].dest, 'tenant')
        self.assertEqual(cmd.option_list[1].dest, 'locale')
        self.assertEqual(cmd.option_list[2].dest, 'compile')
        self.assertEqual(cmd.option_list[3].dest, 'pocmd')

    def test_txtranslate(self):
        from ..management.commands.txtranslate import Command as TxTranslateCommand
        cmd = TxTranslateCommand()

        self.assertEqual(len(cmd.option_list), 5)
        self.assertEqual(cmd.option_list[0].dest, 'tenant')
        self.assertEqual(cmd.option_list[1].dest, 'locale')
        self.assertEqual(cmd.option_list[2].dest, 'compile')
        self.assertEqual(cmd.option_list[3].dest, 'pocmd')
        self.assertEqual(cmd.option_list[4].dest, 'push')

    def test_compilepo(self):
        from ..management.commands.compilepo import Command as CompileCommand
        cmd = CompileCommand()

        self.assertEqual(len(cmd.option_list), 2)
        self.assertEqual(cmd.option_list[0].dest, 'locale')
        self.assertEqual(cmd.option_list[1].dest, 'tenant')


@override_settings(TENANT_APPS=('django_nose',),
                   TENANT_MODEL='client.clients',
                   DATABASE_ROUTERS=('tenant_schemas.routers.TenantSyncRouter',))
class ManagementCommandTests(TestCase):
    def test_translate(self):
        from ..management.commands.txtranslate import Command as TxTranslateCommand
        cmd = TxTranslateCommand()

        with mock.patch('bluebottle.common.management.commands.txtranslate.Command.handle') as handle_mock:
            call_command(cmd, tenant='test', locale='en', compile='test.localhost', 
                         pocmd='test_cmd', push=True)
            args, kwargs = handle_mock.call_args_list[0]
            self.assertEqual(kwargs['tenant'], 'test')
            self.assertEqual(kwargs['locale'], 'en')
            self.assertEqual(kwargs['compile'], 'test.localhost')
            self.assertEqual(kwargs['pocmd'], 'test_cmd')
            self.assertEqual(kwargs['push'], True)

    def test_compilepo(self):
        from ..management.commands.compilepo import Command as CompilepoCommand
        cmd = CompilepoCommand()

        with mock.patch('bluebottle.common.management.commands.compilepo.Command.handle') as handle_mock:
            call_command(cmd, tenant='test', locale='en')

            args, kwargs = handle_mock.call_args_list[0]
            self.assertEqual(kwargs['tenant'], 'test')
            self.assertEqual(kwargs['locale'], 'en')
