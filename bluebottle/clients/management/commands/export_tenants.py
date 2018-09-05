import json

from rest_framework.authtoken.models import Token
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from bluebottle.clients import properties
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant


class Command(BaseCommand):
    help = 'Export tenants, so that we can import them into the accounting app'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, default=None, action='store')

    def handle(self, *args, **options):
        results = []
        for client in Client.objects.all():
            properties.set_tenant(client)
            with LocalTenant(client, clear_tenant=True):
                ContentType.objects.clear_cache()
                accounts = []
                for merchant in properties.MERCHANT_ACCOUNTS:
                    if merchant['merchant'] == 'docdata':
                        if merchant['merchant_name'] == '1procentclub_nw' and client.client_name != 'onepercent':
                            pass
                        else:
                            accounts.append(
                                {
                                    'service_type': 'docdata',
                                    'username': merchant['merchant_name']
                                }
                            )

                api_key = Token.objects.get(user__username='accounting').key
                results.append({
                    "name": client.client_name,
                    "domain": properties.TENANT_MAIL_PROPERTIES['website'],
                    "api_key": api_key,
                    "accounts": accounts
                })
        if options['file']:
            text_file = open(options['file'], "w")
            text_file.write(json.dumps(results))
            text_file.close()
        else:
            print json.dumps(results)
