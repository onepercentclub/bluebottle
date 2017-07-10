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


class Counter(object):
    def __init__(self, total=1):
        self.reset(total=total)

    def inc(self):
        sys.stdout.flush()
        sys.stdout.write("\r{}/{}".format(self.count, self.total))
        self.count += 1

    def reset(self, total=1):
        self.total = total
        self.count = 1


class Command(BaseCommand):
    """
    TODO: json import should:
        * pages:
        ** always include language
    """
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

            counter = Counter()
            for key in ['users', 'categories', 'projects', 'tasks', 'rewards', 'wallposts', 'orders', 'pages']:
                if key in data:
                    print("Importing {}".format(key))
                    counter.reset(total=len(data[key]))
                    for value in data[key]:
                        counter.inc()
                        method_to_call = getattr(self, '_handle_{}'.format(key))
                        method_to_call(value)
                    print(" Done!\n")

    def _generic_import(self, instance, data, excludes=False):
        excludes = excludes or []
        for k in data:
            if k not in excludes and hasattr(instance, k):
                setattr(instance, k, data[k])

    def _handle_users(self, d):
        if 'remote_id' in d:
            user, created = Member.objects.get_or_create(remote_id=d['remote_id'])
        else:
            user, created = Member.objects.get_or_create(email=d['email'])
        self._generic_import(user, d, excludes=['email', 'remote_id'])
        user.save()

    def _handle_categories(self, d):
        cat, created = Category.objects.get_or_create(slug=d['slug'])
        self._generic_import(cat, d, excludes=['slug'])

    def _handle_projects(self, d):
        campaign = ProjectPhase.objects.get(slug='campaign')
        deadline = datetime.datetime.strptime(d['deadline'], '%Y-%m-%d')
        deadline = pytz.utc.localize(deadline)

        project, created = Project.objects.get_or_create(
            slug=d['slug'],
            owner=Member.objects.get(email=d['user']),
            status=campaign
        )
        project.created = d['created'] + 'T12:00:00+01:00'
        project.campaign_started = d['created'] + 'T12:00:00+01:00'
        project.amount_asked = Money(d['goal'], 'EUR')
        project.categories = Category.objects.filter(slug__in=d['categories'])
        project.deadline = deadline

        if 'image' in d:
            content = urllib.urlretrieve(d['image'])
            name = urlparse(d['image']).path.split('/')[-1]
            project.image.save(name, File(open(content[0])), save=True)

        self._generic_import(project, d,
                             excludes=['deadline', 'slug', 'user', 'created', 'goal', 'categories', 'image'])

        try:
            project.save()
        except IntegrityError:
            project.title += '*'
            project.save()

    def _handle_tasks(self, d):
        project = Project.objects.get(slug=d['project'])
        task, created = Task.objects.get_or_create(
            project=project,
            time_needed="8",
            skill__id=1,
            deadline=project.deadline,
            status=Task.TaskStatuses.realized,
            deadline_to_apply=project.deadline,
            title=d['title'],
            people_needed=d['people_needed']
        )
        self._generic_import(task, d, excludes=['project', 'title', 'people_needed'])
        task.save()

    def _handle_rewards(self, d):
        if d['amount']:
            try:
                project = Project.objects.get(slug=d['project'])
                reward, created = Reward.objects.get_or_create(
                    project=project,
                    amount=Money(d['amount'].replace(",", ".") or 0.0, 'EUR'),
                    limit=d['limit'] or 0
                )
                self._generic_import(reward, d, excludes=['amount', 'limit', 'project'])
                reward.save()
            except (Project.DoesNotExist, ValueError):
                pass

    def _handle_wallposts(self, d):
        try:
            project = Project.objects.get(slug=d['project'])
            author = Member.objects.get(email=d['email'])
            created = datetime.datetime.strptime(d['date'], '%Y-%m-%d %H:%M:%S')
            created = pytz.utc.localize(created)
            wallpost, created = TextWallpost.objects.get_or_create(
                object_id=project.id,
                content_type=ContentType.objects.get_for_model(Project),
                created=created,
                author=author
            )
            self._generic_import(wallpost, d, excludes=['project', 'author', 'email'])
            wallpost.save()
        except (Project.DoesNotExist, Member.DoesNotExist, ValueError) as e:
            print(e)
            pass

    def _handle_orders(self, d):
        try:
            user = Member.objects.get(email=d['user'])
        except (TypeError, Member.DoesNotExist):
            user = None
        order = Order.objects.create(user=user)
        if d['completed']:
            try:
                completed = d['completed'] + '+01:00'
            except AttributeError as e:
                print(e)
                print(d['completed'])
                completed = now()
            order.locked()
            order.success()
            order.created = completed
            order.completed = completed
            order.confirmed = completed
        order.save()

        if d['donations']:
            for don in d['donations']:
                try:
                    project = Project.objects.get(title=don['project'])
                except Project.DoesNotExist:
                    project = Project.objects.all()[0]
                donation = Donation.objects.create(project=project,
                                                   order=order,
                                                   amount=Money(don['amount'], 'EUR'))
                donation.save()

    def _handle_pages(self, d):
        author = Member.objects.get(email=d['author'])
        page, created = Page.objects.get_or_create(
            author=author,
            status=Page.PageStatus.published,
            publication_date=now(),
            language='nl'
        )
        d['slug'] = d["slug"] or slugify(d['title'] + author.username)

        self._generic_import(page, d, excludes=['author', 'project', 'content'])
        page.save()

        if created:
            text = TextItem.objects.create(
                parent=page,
                text=d['content']
            )
            text.save()
