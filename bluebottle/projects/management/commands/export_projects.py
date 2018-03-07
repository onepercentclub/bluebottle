import json

from bluebottle.projects.models import Project
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import connection

from bluebottle.clients.models import Client

from bluebottle.clients.utils import LocalTenant


class Command(BaseCommand):
    help = 'Export projects, so that we can import them into the accounting app'

    def add_arguments(self, parser):
        parser.add_argument('--start', type=str, default=None, action='store')
        parser.add_argument('--end', type=str, default=None, action='store')

    def handle(self, *args, **options):
        results = []
        for client in Client.objects.all():
            connection.set_tenant(client)
            with LocalTenant(client, clear_tenant=True):
                ContentType.objects.clear_cache()

                projects = Project.objects.filter(
                    amount_donated__gt=0
                )

                if options['start']:
                    projects = projects.filter(created__gte=options['start'])
                if options['end']:
                    projects = projects.filter(deadline__lte=options['end'])

                for project in projects:
                    started = project.campaign_started if project.campaign_started else project.created
                    ended = project.campaign_ended if project.campaign_ended else project.deadline
                    results.append({
                        'tenant': client.client_name,
                        'id': project.id,
                        'title': project.title,
                        'slug': project.slug,
                        'started': started.strftime('%Y-%m-%d'),
                        'ended': ended.strftime('%Y-%m-%d')
                    })

        print json.dumps(results)
