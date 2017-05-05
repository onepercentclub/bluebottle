import json
from django.core.management.base import BaseCommand
from django.db import connection

from bluebottle.orders.models import Order
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
                orders = Order.objects.filter(status__in=('pending', 'success'))
                if options['start']:
                    orders = orders.filter(created__gte=options['start'])
                if options['end']:
                    orders = orders.filter(created__lte=options['end'])

                for order in orders:
                    results.append({
                        'id': order.id,
                        'transaction_reference': order.payment.transaction_reference,
                        'tenant': client.client_name,
                        'status': order.status,
                        'created': order.created.strftime('%Y-%m-%d'),
                        'amount': {
                            'amount': float(order.total.amount),
                            'currency': str(order.total.currency)
                        },
                        'donations': [{
                            'id': donation.id,
                            'amount': {
                                'amount': float(donation.amount.amount),
                                'currency': str(donation.amount.currency)
                            },
                            'donation_id': donation.pk
                        } for donation in order.donations.all()]
                    })

        print json.dumps(results)
