import json
from django.core.management.base import BaseCommand
from django.db import connection


from bluebottle.payouts.models import ProjectPayout
from bluebottle.clients.models import Client

from bluebottle.clients.utils import LocalTenant


class Command(BaseCommand):
    help = 'Export donations, so that we can import them into the accounting app'

    def add_arguments(self, parser):
        parser.add_argument('--start', type=str, default=None, action='store')
        parser.add_argument('--end', type=str, default=None, action='store')

    def handle(self, *args, **options):
        results = []
        for client in Client.objects.all():
            connection.set_tenant(client)
            with LocalTenant(client, clear_tenant=True):

                payouts = ProjectPayout.objects.all()
                if options['start']:
                    payouts = payouts.filter(created__gte=options['start'])
                if options['end']:
                    payouts = payouts.filter(created__lte=options['end'])

                for payout in payouts:
                    results.append({
                        'id': payout.id,
                        'tenant': client.client_name,
                        'status': payout.status,
                        'created': payout.created.strftime('%Y-%m-%d'),
                        'invoice_reference': payout.invoice_reference,
                        'amount_raised': {
                            'amount': float(payout.amount_raised.amount),
                            'currency': str(payout.amount_raised.currency)
                        },
                        'amount_payable': {
                            'amount': float(payout.amount_payable.amount),
                            'currency': str(payout.amount_payable.currency)
                        },
                        'organization_fee': {
                            'amount': float(payout.organization_fee.amount),
                            'currency': str(payout.organization_fee.currency)
                        },
                        'donations': [{
                            'id': donation.id,
                            'amount': {
                                'amount': float(donation.amount.amount),
                                'currency': str(donation.amount.currency)
                            },
                            'donation_id': donation.pk
                        } for donation in payout.project.donations]
                    })

        print json.dumps(results)
