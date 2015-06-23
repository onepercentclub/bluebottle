from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now
from bluebottle.clients.models import Client
from bluebottle.projects.models import Project
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.tasks.models import Task
from django.db import connection


class Command(BaseCommand):
    args = 'No arguments required'
    help = 'Sets projects to "Done Incomplete" and task status to "Realised" \
            when the deadline is passed'

    def handle(self, *args, **options):

        for client in Client.objects.all():
            self.update_statuses_for_client(client)

    def update_statuses_for_client(self, client):
        """
        Projects which have expired but have been funded will already have
        their status set to done-complete so these can be ignored. We only
        need to update projects which haven't been funded but have expired,
        or they have been overfunded and have expired.
        """
        connection.set_tenant(client)
        self.stdout.write("Checking deadlines for client {0}".
                          format(client.client_name))

        try:
            done_complete_phase = ProjectPhase.objects.get(
                slug='done-complete')
            done_incomplete_phase = ProjectPhase.objects.get(
                slug='done-incomplete')
        except ProjectPhase.DoesNotExist:
            raise CommandError(
                "A ProjectPhase with name 'Done-Complete' or 'Done-Incomplete' \
                does not exist")

        try:
            campaign_phase = ProjectPhase.objects.get(slug='campaign')
        except ProjectPhase.DoesNotExist:
            raise CommandError(
                "A ProjectPhase with name 'Campaign' does not exist")

        try:
            closed_phase = ProjectPhase.objects.get(slug='closed')
        except ProjectPhase.DoesNotExist:
            raise CommandError(
                "A ProjectPhase with slug 'closed' does not exist")

        """
        Projects which have at least the funds asked, are still in campaign
        phase and have not expired need the campaign funded date set to now.
        FIXME: this action should be moved into the code where 'amount_needed'
        is calculated => when the value is lte 0 then set campaign_funded.
        """
        self.stdout.write("Checking Project funded and still running...")
        Project.objects.filter(amount_needed__lte=0,
                               status=campaign_phase,
                               deadline__gt=now()).update(campaign_funded=now())

        """
        Projects which are still in campaign phase but have expired need to be
        set to 'done'.
        """
        self.stdout.write("Checking Project deadlines...")
        for project in Project.objects.filter(status=campaign_phase,
                                              deadline__lte=now()):
            if project.amount_donated >= project.amount_asked:
                project.status = done_complete_phase
            elif project.amount_donated <= 20 or not project.campaign_started:
                project.status = closed_phase
            else:
                project.status = done_incomplete_phase
            project.campaign_ended = now()
            project.save()

        """
        Iterate over tasks and save them one by one so the receivers get a
        signal
        """
        self.stdout.write("Checking Task deadlines...\n\n")
        for task in Task.objects.filter(status='in progress',
                                        deadline__lt=now()).all():

            task.deadline_reached()

        self.stdout.write(
            "Successfully updated the status of expired Project and Task \
              models.\n\n")
