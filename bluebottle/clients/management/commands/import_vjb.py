import json

import datetime
import pytz
from django.db.utils import IntegrityError
from moneyed.classes import Money

from bluebottle.rewards.models import Reward
from bluebottle.tasks.models import Task

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

            for p in data['projects']:
                deadline = datetime.datetime.strptime(p['deadline'], '%Y-%m-%d')
                deadline = pytz.utc.localize(deadline)

                project, created = Project.objects.get_or_create(
                    owner_id=1,
                    slug=p['slug'])
                project.status = campaign
                project.title = p['title']
                project.created = p['created'] + 'T12:00:00+01:00'
                project.campaign_started = p['created'] + 'T12:00:00+01:00'
                project.story = p['description']
                project.pitch = p['pitch']
                project.amount_asked = Money(p['goal'], 'EUR')
                project.video = p['video']
                project.deadline = deadline
                try:
                    project.save()
                except IntegrityError:
                    project.title += '*'
                    project.save()

            for t in data['tasks']:
                try:
                    project = Project.objects.get(slug=t['project'])
                    task, created = Task.objects.get_or_create(
                        project=project,
                        time_needed="8",
                        skill__id=1,
                        deadline=project.deadline,
                        deadline_to_apply=project.deadline,
                        title=t['title']
                    )
                    task.description = t['description'],
                    task.people_needed = t['people_needed'],
                    task.save()
                except (Project.DoesNotExist, TypeError):
                    pass

            for r in data['rewards']:
                try:
                    project = Project.objects.get(slug=r['project'])
                    reward, created = Reward.objects.get_or_create(
                        project=project,
                        title=r['title'],
                    )
                    reward.description = r['description'],
                    reward.amount = Money(r['amount'], 'EUR'),
                    reward.limit = r['limit'],
                    reward.save()
                except Project.DoesNotExist:
                    pass
