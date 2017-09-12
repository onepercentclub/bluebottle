import sys
import datetime
import json
import logging
from urlparse import urlparse

import pytz
from django.db.utils import IntegrityError
from moneyed.classes import Money

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils.text import slugify
from django.utils.timezone import now
from django.contrib.contenttypes.models import ContentType

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
from bluebottle.clients import properties

logger = logging.getLogger(__name__)


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
    help = 'Import data from json'
    upload = None
    models = [
        'users',
        'categories',
        'projects',
        'tasks',
        'rewards',
        'wallposts',
        'orders',
        'pages'
    ]

    def add_arguments(self, parser):
        parser.add_argument('--file', '-f', action='store', dest='file',
                            help="JSON import file.")
        parser.add_argument('--upload', '-u', action='store', dest='upload',
                            required=False, help="Path to uploaded media.")
        parser.add_argument('--tenant', '-t', action='store', dest='tenant',
                            help="The tenant to run the recurring donations for.")
        parser.add_argument('--models', '-m', action='store', dest='models',
                            required=False, nargs='*', choices=self.models,
                            help="Models you want to import, can be multiple e.g. -m users wallposts")

    def handle(self, *args, **options):

        client = Client.objects.get(client_name=options['tenant'])
        connection.set_tenant(client)

        self.upload = options['upload']

        with LocalTenant(client, clear_tenant=True):

            with open(options['file']) as json_file:
                data = json.load(json_file)

            if options['models']:
                self.models = options['models']

            counter = Counter()
            for key in self.models:
                if key in data:
                    logger.info("Importing {}".format(key))
                    counter.reset(total=len(data[key]))
                    for value in data[key]:
                        counter.inc()
                        method_to_call = getattr(self, '_handle_{}'.format(key))
                        method_to_call(value)
                    logger.info(" Done!\n")

    def _generic_import(self, instance, data, excludes=False):
        excludes = excludes or []
        for k in data:
            if k not in excludes and hasattr(instance, k):
                setattr(instance, k, data[k])

    def _handle_users(self, data):
        """Expected fields for Users import:
        email               (string<email>)
        remote_id           (string, optional)
        description         (string)
        verified            (bool)
        username            (string)
        is_staff            (bool)
        is_admin            (bool)
        first_name          (string)
        last_name           (string)
        primary_language    (string)
        """
        if 'remote_id' in data:
            user, _ = Member.objects.get_or_create(remote_id=data['remote_id'])
        else:
            user, _ = Member.objects.get_or_create(email=data['email'])
        self._generic_import(user, data, excludes=['email', 'remote_id'])
        user.save()

    def _handle_categories(self, data):
        """Expected fields for Categories import:
        title       (string)
        slug        (string)
        description (string)
        """
        cat, _ = Category.objects.get_or_create(slug=data['slug'])
        self._generic_import(cat, data, excludes=['slug'])
        cat.save()

    def _handle_projects(self, data):
        """Expected fields for Projects import:
        slug        (string)
        title       (string)
        deadline    (string<date>)
        created     (string<date>)
        user        (string<email>)
        description (string)
        pitch       (string)
        goal        (int)
        video       (string<url>)
        image       (string<url>)
        categories  (array<category-slug>)
        """
        deadline = datetime.datetime.strptime(data['deadline'], '%Y-%m-%d')
        deadline = pytz.utc.localize(deadline)

        try:
            project = Project.objects.get(slug=data['slug'])
        except Project.DoesNotExist:
            project = Project(slug=data['slug'])

        project.owner = Member.objects.get(email=data['user'])
        try:
            project.status = ProjectPhase.objects.get(slug=data['status'])
        except (ProjectPhase.DoesNotExist, KeyError):
            # If we don't have a status, then it should be set in admin, so plan-new seems best.
            project.status = ProjectPhase.objects.get(slug='plan-new')
        project.title = data['title'] or data['slug']
        project.created = data['created'] + 'T12:00:00+01:00'
        project.campaign_started = data['created'] + 'T12:00:00+01:00'
        goal = data['goal'] or 0.0
        project.amount_asked = Money(goal, 'EUR')
        project.deadline = deadline
        project.video_url = data['video']

        self._generic_import(project, data,
                             excludes=['deadline', 'slug', 'user', 'created',
                                       'status', 'goal', 'categories', 'image', 'video'])
        try:
            project.save()
        except IntegrityError:
            project.title = project.title + '*'
        project.categories = Category.objects.filter(slug__in=data['categories'])

        if 'image' in data and data['image'].startswith('http'):
            parts = urlparse(data['image']).path.split('/')
            name = "/".join(parts[3:])
            if not self.upload:
                logger.warn("Upload path not set, can't store project image. Please use -u")
            file_name = u"{}{}".format(self.upload, name)
            try:
                file = open(file_name, 'rb')
                project.image.save(name, File(file), save=True)
            except IOError:
                logger.warn("Couldn't find file {}".format(file_name))

    def _handle_tasks(self, data):
        """Expected fields for Tasks import:
        project         (string<slug>)
        title           (string)
        description     (string)
        people_needed   (int)
        """
        project = Project.objects.get(slug=data['project'])
        task, _ = Task.objects.get_or_create(
            project=project,
            time_needed="8",
            skill__id=1,
            deadline=project.deadline,
            status=Task.TaskStatuses.realized,
            deadline_to_apply=project.deadline,
            title=data['title'],
            people_needed=data['people_needed']
        )
        self._generic_import(task, data, excludes=['project', 'title', 'people_needed'])
        task.save()

    def _handle_rewards(self, data):
        """Expected fields for Rewards import:
        project     (string<slug>)
        title       (string)
        description (string)
        amount      (string)
        text        (string)
        """
        if data['amount']:
            try:
                project = Project.objects.get(slug=data['project'])
                reward, _ = Reward.objects.get_or_create(
                    project=project,
                    title=data['title'],
                    amount=Money(data['amount'] or 0.0, 'EUR'),
                    limit=data['limit'] or 0
                )
                self._generic_import(reward, data, excludes=['amount', 'limit', 'project'])
                reward.save()
            except (Project.DoesNotExist, ValueError):
                pass

    def _handle_wallposts(self, data):
        """Expected fields for Wallpost import:
        project (string<slug>)
        email   (string<email>)
        date    (string<datetime>)
        text    (string)
        """
        try:
            project = Project.objects.get(slug=data['project'])
            author = Member.objects.get(email=data['email'])
            created = datetime.datetime.strptime(data['date'], '%Y-%m-%d %H:%M:%S')
            created = pytz.utc.localize(created)
            wallpost, _ = TextWallpost.objects.get_or_create(
                object_id=project.id,
                content_type=ContentType.objects.get_for_model(Project),
                created=created,
                author=author
            )
            self._generic_import(wallpost, data, excludes=['project', 'author', 'email'])
            wallpost.save()
        except (Project.DoesNotExist, Member.DoesNotExist, ValueError) as err:
            print(err)

    def _handle_orders(self, data):
        """Expected fields for Order import:
        completed   (string<date>)
        user        (string<email>)
        total       (string)
        donations   (array)
            project     (string<title>)
            amount      (float)
            reward      (string<title>)
        """
        try:
            user = Member.objects.get(email=data['user'])
        except (TypeError, Member.DoesNotExist):
            user = None
        order = Order.objects.create(user=user)
        if data['completed']:
            try:
                completed = data['completed'] + '+01:00'
            except AttributeError as err:
                print(err)
                print(data['completed'])
                completed = now()
            order.locked()
            order.success()
            order.created = completed
            order.completed = completed
            order.confirmed = completed
        order.save()

        if data['donations']:
            for don in data['donations']:
                try:
                    project = Project.objects.get(slug=don['project'])
                except Project.DoesNotExist:
                    print "Could not find project {0}".format(don['project'])
                    continue
                try:
                    reward = Reward.objects.get(project=project, title=don['reward'])
                except Reward.MultipleObjectsReturned:
                    reward = Reward.objects.filter(project=project, title=don['reward']).all()[0]
                except (Reward.DoesNotExist, KeyError):
                    reward = None
                donation = Donation.objects.create(project=project,
                                                   reward=reward,
                                                   name=getattr(don, 'name', None),
                                                   order=order,
                                                   amount=Money(don['amount'], 'EUR'))
                donation.save()

    def _handle_pages(self, data):
        """Expected fields for Page import:
        slug     (string)
        title    (string)
        author   (string<email>)
        content  (string)
        language (string, optional)
        """
        author = Member.objects.get(email=data['author'])
        try:
            language = data['language']
        except KeyError:
            language = properties.LANGUAGE_CODE

        page, created = Page.objects.get_or_create(
            author=author,
            status=Page.PageStatus.published,
            publication_date=now(),
            language=language
        )

        # TODO: add the slug generation to the Page model
        data['slug'] = data["slug"] or slugify(data['title'] + author.username)

        self._generic_import(page, data, excludes=['author', 'content'])
        page.save()

        if created:
            text = TextItem.objects.create(
                parent=page,
                text=data['content']
            )
            text.save()
