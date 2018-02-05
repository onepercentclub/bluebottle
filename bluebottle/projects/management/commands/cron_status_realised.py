from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.projects.models import Project
from bluebottle.tasks.models import Task


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
        with LocalTenant(client, clear_tenant=True):

            self.stdout.write("Checking deadlines for client {0}".
                              format(client.client_name))

            # we no longer need the actual phases (moved to project)
            # but verify they exist, just to be sure
            try:
                ProjectPhase.objects.get(slug='done-complete')
                ProjectPhase.objects.get(slug='done-incomplete')
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
                ProjectPhase.objects.get(slug='closed')
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
            for project in Project.objects.filter(status=campaign_phase, deadline__gt=now()):
                if project.amount_needed.amount <= 0:
                    project.campaign_funded = now()
                    project.save()

            """
            Projects which are still in campaign phase but have expired need to be
            set to 'done'.
            """
            self.stdout.write("Checking Project deadlines...")
            for project in Project.objects.filter(status=campaign_phase,
                                                  deadline__lte=now()):
                project.deadline_reached()

            """
            Iterate over tasks and save them one by one so the receivers get a
            signal
            """
            self.stdout.write("Checking Task deadlines...\n\n")

            for task in Task.objects.filter(
                    status__in=['in progress', 'open', 'full'],
                    project__status__slug__in=['campaign', 'done-complete', 'done-incomplete'],
                    deadline_to_apply__lt=now()).all():
                task.deadline_to_apply_reached()

            for task in Task.objects.filter(
                    status__in=['in progress', 'open', 'full'],
                    project__status__slug__in=['campaign', 'done-complete', 'done-incomplete'],
                    deadline__lt=now()).all():
                task.deadline_reached()

            self.stdout.write(
                "Successfully updated the status of expired projects and Tasks")

            self.stdout.write("Checking projects with voting deadlines\n\n")

            vote_phase = ProjectPhase.objects.get(slug='voting')
            vote_done = ProjectPhase.objects.get(slug='voting-done')

            for project in Project.objects.filter(status=vote_phase,
                                                  voting_deadline__lt=now()):
                project.status = vote_done
                project.save()

            self.stdout.write("Done checking projects with voting deadlines")
