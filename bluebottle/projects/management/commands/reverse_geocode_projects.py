from django.db import connection
from django.core.management.base import BaseCommand

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.projects.models import Project, ProjectLocation


class Command(BaseCommand):
    args = 'No arguments required'
    help = 'Set project location based on geo location'

    def handle(self, *args, **options):
        for client in Client.objects.all():
            connection.set_tenant(client)
            with LocalTenant(client, clear_tenant=True):
                for project in Project.objects.filter(
                    latitude__isnull=False,
                    longitude__isnull=False,
                    projectlocation__isnull=True
                ):
                    ProjectLocation.objects.create(
                        project=project,
                        latitude=project.latitude,
                        longitude=project.longitude
                    )
