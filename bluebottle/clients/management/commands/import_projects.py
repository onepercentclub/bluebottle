import json

from bluebottle.bb_projects.models import ProjectPhase

from django.core.management.base import BaseCommand
from django.db import connection

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant


from bluebottle.projects.models import Project


class Command(BaseCommand):
    help = 'Import Projects from json'

    def add_arguments(self, parser):
        parser.add_argument('file')
        parser.add_argument('--tenant', '-t', action='store', dest='tenant',
                            help="The tenant to run the recurring donations for.")

    def handle(self, *args, **options):

        client = Client.objects.get(client_name=options['tenant'])
        connection.set_tenant(client)

        with LocalTenant(client, clear_tenant=True):

            with open(options['file']) as json_file:
                data = json.load(json_file)

            campaign = ProjectPhase.objects.get(slug='campaign')

            for p in data:
                project, created = Project.objects.get_or_create(
                    owner_id=1,
                    slug=p['slug'],
                    status=campaign)
                project.title = p['title']
                project.created = p['created']
                project.description = p['description']
                project.pitch = p['pitch']
                project.save()
