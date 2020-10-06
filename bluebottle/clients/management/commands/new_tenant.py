# coding=utf-8
from builtins import input
from optparse import make_option

from django.core import exceptions
from django.utils.encoding import force_str
from django.conf import settings
from django.db.utils import IntegrityError
from django.core.management import call_command

from tenant_schemas.utils import get_tenant_model

from bluebottle.members.models import Member
from bluebottle.common.management.commands.base import Command as BaseCommand
from bluebottle.utils.models import Language


class Command(BaseCommand):
    help = 'Create a tenant'

    option_list = BaseCommand.options + (
        make_option('--full-name',
                    help='Specifies the full name for the tenant (e.g. "Our New Tenant").'),
        make_option('--schema-name',
                    help='Specifies the schema name for the tenant (e.g. "new_tenant").'),
        make_option('--domain-url',
                    help='Specifies the domain_url for the tenant (e.g. "new-tenant.localhost").'),
        make_option('--client-name',
                    help='Specifies the client name for the tenant (e.g. "new-tenant").'),
        make_option('--languages',
                    default='en',
                    help='Specifies the client languages (e.g. "en,nl").'),
        make_option('--post-command',
                    help='Calls another management command after the tenant is created.')
    )

    def handle(self, *args, **options):
        name = options.get('full_name', None)
        client_name = options.get('client_name', None)
        schema_name = options.get('schema_name', None)
        domain_url = options.get('domain_url', None)
        languages = options.get('languages', 'en')
        post_command = options.get('post_command', None)

        # If full-name is specified then don't prompt for any values.
        if name:
            if not client_name:
                client_name = ''.join(ch if ch.isalnum() else '-' for ch in name).lower()
            if not schema_name:
                schema_name = client_name.replace('-', '_')
            if not domain_url:
                base_domain = getattr(settings, 'TENANT_BASE_DOMAIN', 'localhost')
                domain_url = '{0}.{1}'.format(client_name, base_domain)

            client_name.replace('_', '-')

            client = self.store_client(
                name=name,
                client_name=client_name,
                domain_url=domain_url,
                schema_name=schema_name
            )

            if client is False:
                return

            if not client:
                name = None

        while name is None:
            if not name:
                input_msg = 'Tenant name'
                name = eval(input(force_str('%s: ' % input_msg)))

            default_client_name = ''.join(ch if ch.isalnum() else '-' for ch in name).lower()
            default_schema_name = default_client_name.replace('-', '_')
            base_domain = getattr(settings, 'TENANT_BASE_DOMAIN', 'localhost')
            default_domain_url = '{0}.{1}'.format(default_client_name, base_domain)

            while client_name is None:
                if not client_name:
                    input_msg = 'Client name'
                    input_msg = "%s (leave blank to use '%s')" % (input_msg, default_client_name)
                    client_name = eval(input(force_str('%s: ' % input_msg))) or default_client_name

            while schema_name is None:
                if not schema_name:
                    input_msg = 'Database schema name'
                    input_msg = "%s (leave blank to use '%s')" % (input_msg, default_schema_name)
                    schema_name = eval(input(force_str('%s: ' % input_msg))) or default_schema_name

            while domain_url is None:
                if not domain_url:
                    input_msg = 'Domain url'
                    input_msg = "%s (leave blank to use '%s')" % (input_msg, default_domain_url)
                    domain_url = eval(input(force_str('%s: ' % input_msg))) or default_domain_url

            client_name.replace('_', '-')

            client = self.store_client(
                name=name,
                client_name=client_name,
                domain_url=domain_url,
                schema_name=schema_name
            )
            if client is False:
                break

            if not client:
                name = None
                continue

        if client and client_name:
            from django.db import connection
            connection.set_tenant(client)
            self.create_languages(languages)
            self.create_client_superuser()
            call_command('loaddata', 'geo_data')
            call_command('loaddata', 'geo_data')
            call_command('loaddata', 'skills')
            call_command('search_index', '--rebuild', '-f')
            call_command('loadlinks', '-f', 'links.json')
            call_command('loadpages', '-f', 'pages.json')

        if client and post_command:
            call_command(post_command, *args, **options)

        return

    def create_languages(self, languages):
        for lang in languages.split(","):
            if lang == 'nl':
                Language.objects.get_or_create(
                    code='nl',
                    defaults={
                        'language_name': 'Dutch',
                        'native_name': 'Nederlands'

                    }
                )
            if lang == 'en':
                Language.objects.get_or_create(
                    code='en',
                    defaults={
                        'language_name': 'English',
                        'native_name': 'English'

                    }
                )
            if lang == 'fr':
                Language.objects.get_or_create(
                    code='fr',
                    defaults={
                        'language_name': 'French',
                        'native_name': 'Français'
                    }
                )

    def create_client_superuser(self):
        password = 'pbkdf2_sha256$12000$MKnW1lFPvfhP$IFidWIsLSjfaWErZa4NFK2N40kbdYhn4PiebBGIgMLg='
        su = Member.objects.create(first_name='admin',
                                   last_name='example',
                                   email='admin@example.com',
                                   password=password,
                                   is_active=True,
                                   is_staff=True,
                                   is_superuser=True)
        su.save()

    def store_client(self, name, client_name, domain_url, schema_name):
        try:
            client = get_tenant_model().objects.create(
                name=name,
                client_name=client_name,
                domain_url=domain_url.split(":", 1)[0],  # strip optional port
                schema_name=schema_name
            )
            client.save()
            return client
        except exceptions.ValidationError as e:
            self.stderr.write("Error: %s" % '; '.join(e.messages))
            name = None
            return False
        except IntegrityError as e:
            self.stderr.write("Error: We've already got a tenant with that name or property.")
            return False
