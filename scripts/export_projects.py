import json

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from bluebottle.projects.models import Project


def run(*args):
    projects = []
    for client in Client.objects.all():
        with LocalTenant(client):
            client_name = client.client_name

            for pk, funding_id in Project.objects.filter(
                payout_status__isnull=False
            ).values_list('pk', 'funding_id'):
                projects.append((client_name, pk, funding_id))

    print json.dumps(projects)
