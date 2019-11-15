import json

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from bluebottle.donations.models import Donation


def run(*args):
    donations = []
    for client in Client.objects.all():
        with LocalTenant(client):
            client_name = client.client_name

            for pk, funding_id in Donation.objects.filter(
                project__payout_status__isnull=False
            ).values_list('pk', 'new_donation_id'):
                donations.append((client_name, pk, funding_id))

    print json.dumps(donations)
