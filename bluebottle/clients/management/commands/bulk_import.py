import datetime
import json

from django.contrib.contenttypes.models import ContentType
from moneyed.classes import Money
import pytz
import sys
import urllib
from urlparse import urlparse

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import IntegrityError
from django.utils.text import slugify
from django.utils.timezone import now

from fluent_contents.plugins.text.models import TextItem

from bluebottle.categories.models import Category
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.donations.models import Donation
from bluebottle.members.models import Member
from bluebottle.orders.models import Order
from bluebottle.pages.models import Page
from bluebottle.projects.models import Project
from bluebottle.rewards.models import Reward
from bluebottle.tasks.models import Task
from bluebottle.wallposts.models import TextWallpost


class Command(BaseCommand):
    help = 'Import data from json'

    def add_arguments(self, parser):
        parser.add_argument('--file', '-f', action='store', dest='file',
                            help="JSON import file.")
        parser.add_argument('--tenant', '-t', action='store', dest='tenant',
                            help="The tenant to run the recurring donations for.")

    def handle(self, *args, **options):
        client = Client.objects.get(client_name=options['tenant'])
        connection.set_tenant(client)

        with LocalTenant(client, clear_tenant=True):

            with open(options['file']) as json_file:
                data = json.load(json_file)

            campaign = ProjectPhase.objects.get(slug='campaign')

            if 'users' in data:
                print("Importing users")
                t = 1
                for u in data['users']:
                    sys.stdout.flush()
                    str = "\r{}/{}".format(t, len(data['users']))
                    sys.stdout.write(str)
                    t += 1
                    if 'remote_id' in u:
                        user, created = Member.objects.get_or_create(remote_id=u['remote_id'])
                    else:
                        user, created = Member.objects.get_or_create(email=u['email'])
                    for k in u:
                        if hasattr(user, k):
                            setattr(user, k, u[k])
                    user.save()
                print(" Done!\n")

            if 'categories' in data:
                print("Importing categories")
                t = 1
                for c in data['categories']:
                    sys.stdout.flush()
                    str = "\r{}/{}".format(t, len(data['categories']))
                    sys.stdout.write(str)
                    t += 1
                    cat, created = Category.objects.get_or_create(slug=c['slug'])
                    cat.title = c['title']
                    cat.save()
                print(" Done!\n")

            if 'projects' in data:
                print("Importing projects")
                t = 1
                for p in data['projects']:
                    sys.stdout.flush()
                    str = "\r{}/{}".format(t, len(data['projects']))
                    sys.stdout.write(str)
                    t += 1
                    deadline = datetime.datetime.strptime(p['deadline'], '%Y-%m-%d')
                    deadline = pytz.utc.localize(deadline)

                    project, created = Project.objects.get_or_create(
                        slug=p['slug'],
                        owner=Member.objects.get(email=p['user']),
                        status=campaign
                    )
                    project.title = p['title']
                    project.created = p['created'] + 'T12:00:00+01:00'
                    project.campaign_started = p['created'] + 'T12:00:00+01:00'
                    project.story = p['description']
                    project.pitch = p['pitch']
                    project.amount_asked = Money(p['goal'], 'EUR')
                    project.video = p['video']
                    project.deadline = deadline
                    project.categories = Category.objects.filter(slug__in=p['categories'])

                    if 'image' in p:
                        content = urllib.urlretrieve(p['image'])
                        name = urlparse(p['image']).path.split('/')[-1]
                        project.image.save(name, File(open(content[0])), save=True)

                    try:
                        project.save()
                    except IntegrityError:
                        project.title += '*'
                        project.save()

                print(" Done!\n")

            if 'tasks' in data:
                print("Importing tasks")
                i = 1
                for t in data['tasks']:
                    sys.stdout.flush()
                    str = "\r{}/{}".format(i, len(data['tasks']))
                    sys.stdout.write(str)
                    i += 1
                    try:
                        project = Project.objects.get(slug=t['project'])
                        task, created = Task.objects.get_or_create(
                            project=project,
                            time_needed="8",
                            skill__id=1,
                            deadline=project.deadline,
                            status=Task.TaskStatuses.realized,
                            deadline_to_apply=project.deadline,
                            title=t['title'],
                            people_needed=t['people_needed']
                        )
                        task.description = t['description'],
                        task.save()
                    except (Project.DoesNotExist, TypeError):
                        pass
                print(" Done!\n")

            if 'rewards' in data:
                print("Importing rewards")
                t = 1
                for r in data['rewards']:
                    sys.stdout.flush()
                    str = "\r{}/{}".format(t, len(data['rewards']))
                    sys.stdout.write(str)
                    t += 1
                    if r['amount']:
                        try:
                            project = Project.objects.get(slug=r['project'])
                            reward, created = Reward.objects.get_or_create(
                                project=project,
                                title=r['title'],
                                description=r['description'],
                                amount=Money(r['amount'].replace(",", ".") or 0.0, 'EUR'),
                                limit=r['limit'] or 0
                            )
                            reward.save()
                        except (Project.DoesNotExist, ValueError):
                            pass
                print(" Done!\n")

            if 'wallposts' in data:
                print("Importing wallposts")
                t = 1
                for w in data['wallposts']:
                    sys.stdout.flush()
                    str = "\r{}/{}".format(t, len(data['wallposts']))
                    sys.stdout.write(str)
                    t += 1
                    try:
                        project = Project.objects.get(slug=w['project'])
                        author = Member.objects.get(email=w['email'])
                        created = datetime.datetime.strptime(w['date'], '%Y-%m-%d %H:%M:%S')
                        created = pytz.utc.localize(created)
                        wallpost, created = TextWallpost.objects.get_or_create(
                            object_id=project.id,
                            content_type=ContentType.objects.get_for_model(Project),
                            text=w['text'],
                            created=created,
                            author=author
                        )
                        wallpost.save()
                    except (Project.DoesNotExist, Member.DoesNotExist, ValueError) as e:
                        print e
                        pass
                print(" Done!\n")

            if 'orders' in data:
                print("Importing orders/donations")
                t = 1
                for o in data['orders']:
                    sys.stdout.flush()
                    str = "\r{}/{}".format(t, len(data['orders']))
                    sys.stdout.write(str)
                    t += 1
                    try:
                        user = Member.objects.get(email=o['user'])
                    except (TypeError, Member.DoesNotExist):
                        user = None
                    order = Order.objects.create(user=user)
                    if o['completed']:
                        try:
                            completed = o['completed'] + '+01:00'
                        except AttributeError as e:
                            print(e)
                            print(o['completed'])
                            completed = now()
                        order.locked()
                        order.success()
                        order.created = completed
                        order.completed = completed
                        order.confirmed = completed
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
                print(" Done!\n")

            if 'pages' in data:
                print("Importing pages")
                t = 1
                for p in data['pages']:
                    sys.stdout.flush()
                    str = "\r{}/{}".format(t, len(data['pages']))
                    sys.stdout.write(str)
                    t += 1
                    author = Member.objects.get(email=p['author'])
                    page, created = Page.objects.get_or_create(
                        title=p['title'],
                        author=author,
                        status=Page.PageStatus.published,
                    )
                    page.publication_date = now()
                    page.language = 'nl'
                    page.slug = p['slug'] or slugify(p['title'] + author.username)
                    page.save()
                    if created:
                        text = TextItem.objects.create(
                            parent=page,
                            text=p['content']
                        )
                        text.save()
                    page.save()
                print(" Done!\n")
