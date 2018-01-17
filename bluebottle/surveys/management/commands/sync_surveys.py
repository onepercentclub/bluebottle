from bluebottle.clients import properties
from django.core.management.base import BaseCommand

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.surveys.adapters import SurveyGizmoAdapter


class Command(BaseCommand):
    args = 'No arguments required'
    help = 'Synchronize surveys with survey service (SurveyGizmo).'

    def handle(self, *args, **options):

        for client in Client.objects.all():
            self.sync_surveys_for_client(client)

    def sync_surveys_for_client(self, client):
        """
        """
        with LocalTenant(client, clear_tenant=True):

            if properties.SURVEYGIZMO_API_TOKEN:
                self.stdout.write("Synchronizing surveys for client {0}".
                                  format(client.client_name))

                survey_adapter = SurveyGizmoAdapter()
                survey_adapter.update_surveys()
                self.stdout.write("Done synchronizing")
            else:
                self.stdout.write("No survey server configured for client {0}".
                                  format(client.client_name))
