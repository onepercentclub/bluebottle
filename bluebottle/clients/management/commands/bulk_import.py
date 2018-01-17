import sys

from bluebottle.payments.models import OrderPayment
from dateutil import parser
import json
import logging

from django.db.utils import IntegrityError
from moneyed.classes import Money

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.contrib.contenttypes.models import ContentType

from bluebottle.categories.models import Category
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.bb_projects.models import ProjectPhase, ProjectTheme
from bluebottle.donations.models import Donation
from bluebottle.geo.models import Country, Location
from bluebottle.members.models import Member, CustomMemberFieldSettings
from bluebottle.orders.models import Order
from bluebottle.projects.models import Project
from bluebottle.rewards.models import Reward
from bluebottle.tasks.models import Task
from bluebottle.wallposts.models import TextWallpost

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
        'themes',
        'projects',
        'tasks',
        'rewards',
        'wallposts',
        'orders'
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

            if 'orders' in self.models:
                for project in Project.objects.exclude(status__slug='plan-new').all():
                    if project.deadline < now():
                        project.status = ProjectPhase.objects.get(slug='campaign')
                        project.campaign_ended = None
                        project.save()

    def _generic_import(self, instance, data, excludes=False):
        excludes = excludes or []
        for k in data:
            if k not in excludes:
                if hasattr(instance, k):
                    setattr(instance, k, data[k])
                if k.startswith('extra.'):
                    try:
                        field = CustomMemberFieldSettings.objects.get(name=k.replace('extra.', ''))
                    except CustomMemberFieldSettings.DoesNotExist:
                        raise ImportError("Coud not find CustomMemberField {}".format(k.replace('extra.', '')))
                    extra, _ = instance.extra.get_or_create(field=field)
                    extra.value = data[k]
                    extra.save()

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
            try:
                user, _ = Member.objects.get_or_create(remote_id=data['remote_id'])
            except Member.MultipleObjectsReturned:
                raise ImportError('Multiple users for remote_id {}'.format(data['remote_id']))
            if 'email' in data:
                user.email = data['email']
            else:
                user.email = 'temp+' + data['remote_id'] + '@example.com'
        else:
            user, _ = Member.objects.get_or_create(email=data['email'])

        user.is_active = True

        if 'location' in data:
            loc, _ = Location.objects.get_or_create(name=data['location'])
            user.location = loc

        self._generic_import(user, data, excludes=['email', 'remote_id', 'location'])
        user.save()

    def _handle_categories(self, data):
        """Expected fields for Categories import:
        title       (string)
        slug        (string)
        description (string)
        """
        cat, _ = Category.objects.get_or_create(slug=data['slug'])
        self._generic_import(cat, data, excludes=['slug'])
        try:
            cat.save()
        except IntegrityError:
            cat.title = cat.title + '*'
            cat.save()

    def _handle_themes(self, data):
        """Expected fields for Theme import:
        name       (string)
        slug        (string)
        """
        theme, _ = ProjectTheme.objects.get_or_create(slug=data['slug'])
        self._generic_import(theme, data, excludes=['slug'])
        try:
            theme.save()
        except IntegrityError:
            theme.name = theme.name + '*'
            theme.save()

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
        try:
            project = Project.objects.get(slug=data['slug'])
        except Project.DoesNotExist:
            project = Project(slug=data['slug'])
        try:
            project.owner = Member.objects.get(email=data['user'])
        except Member.DoesNotExist:
            project.owner, new = Member.objects.get_or_create(email='admin@example.com')
            if new:
                project.owner.is_active = True
                project.owner.username = 'Admin'
                project.owner.first_name = 'Admin'
                project.owner.last_name = 'Example'
                project.owner.save()

        try:
            project.status = ProjectPhase.objects.get(slug=data['status'])
        except (ProjectPhase.DoesNotExist, KeyError):
            # If we don't have a status, then it should be set in admin, so plan-new seems best.
            project.status = ProjectPhase.objects.get(slug='plan-new')
        deadline = data['deadline']
        if deadline:
            deadline = parser.parse(deadline)

        project.title = data['title'] or data['slug']
        project.created = data['created']
        project.campaign_started = data['created']
        goal = data['goal'] or 0.0
        project.amount_asked = Money(goal, 'EUR')
        project.deadline = deadline
        project.video_url = data['video']
        if data.get('country'):
            project.country = Country.objects.get(alpha2_code=data['country'])
        else:
            project.country = Country.objects.get(alpha2_code='NL')

        self._generic_import(project, data,
                             excludes=['deadline', 'slug', 'user', 'created', 'theme', 'country',
                                       'status', 'goal', 'categories', 'image', 'video'])

        if data.get('theme'):
            try:
                project.theme = ProjectTheme.objects.get(slug=data['theme'])
            except ProjectTheme.DoesNotExist:
                logger.warn("Couldn't find theme {}".format(data['theme']))

        try:
            project.save()
        except IntegrityError:
            project.title = project.title + '*'
            project.save()

        project.categories = Category.objects.filter(slug__in=data['categories'])

        if 'image' in data:
            parts = data['image'].split('/')
            name = "/".join(parts[5:])
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
        try:
            project = Project.objects.get(slug=data['project'])
        except Project.DoesNotExist:
            logger.warn("Couldn't find project {}".format(data['project']))
            return
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
        self._generic_import(task, data, excludes=['project', 'title', 'people_needed', 'time_needed'])
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
                reward.description = reward.description[:500]
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
            created = data['date']
            wallpost, _ = TextWallpost.objects.get_or_create(
                object_id=project.id,
                content_type=ContentType.objects.get_for_model(Project),
                created=created,
                author=author
            )
            self._generic_import(wallpost, data, excludes=['project', 'author', 'email', 'created'])
            wallpost.created = created
            wallpost.save()
        except (Project.DoesNotExist, Member.DoesNotExist, ValueError) as err:
            logger.warn(err)

    def _handle_orders(self, data):
        """Expected fields for Order import:
        completed   (string<date>)
        user        (string<email>)
        total       (string)
        donations   (array)
            project     (string<title>)
            amount      (float)
            reward      (string<title>)
            name        (string)
        """
        try:
            user = Member.objects.get(email=data['user'])
        except (TypeError, Member.DoesNotExist):
            user = None
        completed = data['completed']
        created = data['created']
        total = data['total']
        order, new = Order.objects.get_or_create(user=user, created=created, total=total, completed=completed)
        if new:
            if data['donations']:
                for don in data['donations']:
                    try:
                        project = Project.objects.get(slug=don['project'])
                    except Project.DoesNotExist:
                        print "Could not find project {0}".format(don['project'])
                        continue
                    try:
                        reward = project.reward_set.get(title=don['reward'])
                    except Reward.MultipleObjectsReturned:
                        reward = project.reward_set.filter(title=don['reward']).all()[0]
                    except (Reward.DoesNotExist, KeyError):
                        reward = None
                    donation = Donation.objects.create(
                        project=project,
                        reward=reward,
                        name=don.get('name', '')[:199],
                        order=order,
                        amount=Money(don['amount'], 'EUR'))
                    Donation.objects.filter(pk=donation.pk).update(
                        created=created,
                        updated=completed or created
                    )

            order_payment = OrderPayment.objects.create(order=order)
            order_payment.payment_method = 'externalLegacy'

            OrderPayment.objects.filter(pk=order_payment.pk).update(
                created=created,
                status='settled',
                closed=completed
            )

            Order.objects.filter(pk=order.pk).update(
                created=created,
                status='success',
                updated=completed or created,
                confirmed=completed,
                completed=completed
            )
