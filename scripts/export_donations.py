import json

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from bluebottle.donations.models import Donation


def run(*args):
    donations = []
    for client in Client.objects.all():
        with LocalTenant(client):

            donations += Donation.objects.filter(
                project__payout_status__isnull=False
            ).values('pk', 'new_donation_id')

    print json.dumps(dict((item['pk'], item['new_donation_id']) for item in donations))
