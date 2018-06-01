import json

from django.core.management.base import BaseCommand, CommandError

from rest_framework.authtoken.models import Token

from bluebottle.clients.models import Client
from bluebottle.clients import properties
from bluebottle.clients.utils import LocalTenant


class Command(BaseCommand):
    help = 'Export auth token(s) for a specific user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str)

        parser.add_argument(
            '--tenant',
            type=str,
            action='store',
            dest='tenant',
            default=False,
            help='Export token for specific tenant',
        )

        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            default=False,
            help='Export tokens for all tenants',
        )

    def handle(self, *args, **options):
        if options['all'] and options['tenant']:
            raise CommandError('--all and --tenant cannot be used together')

        if options['all']:
            tenants = Client.objects.all()
        else:
            tenants = Client.objects.filter(client_name=options['tenant'])

        tokens = []
        for tenant in tenants:
            with LocalTenant(tenant):
                tokens += [
                    {
                        'api_key': token.key,
                        'name': tenant.client_name,
                        'domain': 'https://{}'.format(tenant.domain_url),
                        'fees': {
                            'under_target': properties.PROJECT_PAYOUT_FEES.get('not_fully_funded', 0),
                            'over_target': properties.PROJECT_PAYOUT_FEES.get('fully_funded', 0)
                        }
                    } for token in
                    Token.objects.filter(user__email=options['email'])
                ]

        self.stdout.write(json.dumps(tokens, indent=4))
