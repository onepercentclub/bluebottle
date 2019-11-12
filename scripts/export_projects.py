import json

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from bluebottle.projects.models import Project


def run(*args):
    projects = []
    for client in Client.objects.all():
        with LocalTenant(client):
            projects += Project.objects.filter(
                payout_status__isnull=False
            ).values('pk', 'funding_id')

    print json.dumps(dict((item['pk'], item['funding_id']) for item in projects))
