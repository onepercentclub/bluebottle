import json

import datetime
import pytz
from bluebottle.donations.models import Donation

from bluebottle.members.models import Member
from django.db.utils import IntegrityError
from moneyed.classes import Money

from bluebottle.orders.models import Order
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

            for u in data['users']:
                user, created = Member.objects.get_or_create(email=u['email'], remote_id=u['remote_id'])
                user.password = u['password']
                user.first_name = u['first_name']
                user.last_name = u['last_name']
                user.username = u['username']
                user.about_me = u['description']
                user.save()

            for p in data['projects']:
                deadline = datetime.datetime.strptime(p['deadline'], '%Y-%m-%d')
                deadline = pytz.utc.localize(deadline)

                project, created = Project.objects.get_or_create(slug=p['slug'])
                try:
                    project.owner = Member.objects.get(email=p['user'])
                except Member.DoesNotExist:
                    project.owner_id = 1
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
                        title=r['title'][0:30],
                    )
                    reward.description = r['description'],
                    reward.amount = Money(r['amount'], 'EUR'),
                    reward.limit = r['limit'],
                    reward.save()
                except Project.DoesNotExist:
                    pass

            for o in data['orders']:
                try:
                    user = Member.objects.get(email=o['user']['email'])
                except TypeError:
                    user = None
                order = Order.objects.create(user=user)
                if o['completed']:
                    order.locked()
                    order.success()
                    order.created = o['completed']
                    order.completed = o['completed']
                    order.confirmed = o['completed']
                order.save()

                if o['donations']:
                    for don in o['donations']:
                        try:
                            project = Project.objects.get(title=don['project'])
                        except Project.DoesNotExist:
                            project = Project.objects.all()[0]
                        donation = Donation.objects.create(project=project,
                                                           order=order,
                                                           amount=Money(don['amount'], 'EUR'))
                        donation.save()
