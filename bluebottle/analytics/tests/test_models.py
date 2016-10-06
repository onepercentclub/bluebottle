from mock import patch
from decimal import Decimal

from bluebottle.test.utils import BluebottleTestCase
from django.test.utils import override_settings

from bluebottle.projects.models import Project
from bluebottle.tasks.models import Task, TaskMember
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectThemeFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.votes import VoteFactory
from bluebottle.test.factory_models.wallposts import TextWallpostFactory, SystemWallpostFactory, ReactionFactory
from bluebottle.test.factory_models.geo import LocationFactory, CountryFactory

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.analytics import signals
from bluebottle.analytics.backends import InfluxExporter

from .common import FakeInfluxDBClient


def fake_trans(str):
    if str == 'Cleaning the beach':
        return 'Cleaning the park'
    return str


fake_client = FakeInfluxDBClient()


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
@patch.object(InfluxExporter, 'client', fake_client)
class TestProjectAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestProjectAnalytics, self).setUp()
        self.init_projects()

        self.theme = ProjectThemeFactory.create(name='Cleaning the beach',
                                                slug='cleaning-the-beach')
        self.country = CountryFactory.create()
        self.status = ProjectPhase.objects.get(slug='campaign')
        self.expected_tags = {
            'status': self.status.name,
            'theme_slug': u'cleaning-the-beach',
            'status_slug': self.status.slug,
            'country': self.country.name,
            'theme': u'Cleaning the beach',
            'location': '',
            'location_group': '',
            'type': 'project',
            'sub_type': 'funding',
            'tenant': u'test',
        }

    def test_country_tag(self, queue_mock):
        ProjectFactory.create(theme=self.theme, status=self.status,
                              country=self.country, location=None)

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], self.expected_tags)

    def test_location_country_tag(self, queue_mock):
        location = LocationFactory.create()
        ProjectFactory.create(theme=self.theme, status=self.status,
                              location=location, country=None)

        self.expected_tags['country'] = location.country.name
        self.expected_tags['location'] = location.name
        self.expected_tags['location_group'] = location.group.name
        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], self.expected_tags)

    def test_tags_generation(self, queue_mock):
        project = ProjectFactory.create(theme=self.theme, status=self.status,
                              country=self.country)

        self.expected_fields = {
            'id': project.id,
            'user_id': project.owner.id
        }

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], self.expected_tags)
        self.assertEqual(kwargs['fields'], self.expected_fields)

    @patch.object(signals, '_', fake_trans)
    def test_tags_translated(self, queue_mock):
        ProjectFactory.create(theme=self.theme, status=self.status,
                              country=self.country)

        # Simple translation added via fake_trans method above
        self.expected_tags['theme'] = 'Cleaning the park'
        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], self.expected_tags)

    def test_unchanged_status(self, queue_mock):
        project = ProjectFactory.create(theme=self.theme, status=self.status,
                                        country=self.country)
        previous_call_count = queue_mock.call_count

        # Update record without changing status
        project.title = 'A new title'
        project.save()

        self.assertEqual(previous_call_count, queue_mock.call_count,
                         'Analytics should only be sent when status changes')

    def test_bulk_status_change(self, queue_mock):
        for i in range(10):
            ProjectFactory.create(theme=self.theme, country=self.country)

        previous_call_count = queue_mock.call_count
        Project.objects.update(status=self.status)

        self.assertEqual(queue_mock.call_count, previous_call_count + len(Project.objects.all()),
                         'Analytics should be sent when update is called')

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], self.expected_tags)


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
@patch.object(InfluxExporter, 'client', fake_client)
class TestTaskAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestTaskAnalytics, self).setUp()
        self.init_projects()

    def test_tags_generation(self, queue_mock):
        user = BlueBottleUserFactory.create()
        task = TaskFactory.create(author=user)
        project = task.project
        expected_tags = {
            'type': 'task',
            'tenant': u'test',
            'status': 'open',
            'location': '',
            'location_group': '',
            'theme': project.theme.name,
            'theme_slug': project.theme.slug,
        }
        expected_fields = {
            'id': task.id,
            'user_id': task.author.id
        }
        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], expected_tags)
        self.assertEqual(kwargs['fields'], expected_fields)

    def test_unchanged_status(self, queue_mock):
        user = BlueBottleUserFactory.create()
        task = TaskFactory.create(author=user)
        previous_call_count = queue_mock.call_count

        # Update record without changing status
        task.title = 'Let it be white as snow!'
        task.save()

        self.assertEqual(previous_call_count, queue_mock.call_count,
                         'Analytics should only be sent when status changes')

    @patch.object(signals, '_', fake_trans)
    def test_theme_translated(self, queue_mock):
        theme = ProjectThemeFactory.create(name='Cleaning the beach',
                                           slug='cleaning-the-beach')
        project = ProjectFactory.create(theme=theme)
        user = BlueBottleUserFactory.create()
        task = TaskFactory.create(author=user, project=project)

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags']['theme'], 'Cleaning the park')

    def test_bulk_status_change(self, queue_mock):
        for i in range(10):
            TaskFactory.create()

        previous_call_count = queue_mock.call_count
        Task.objects.update(status='realized')

        self.assertEqual(queue_mock.call_count, previous_call_count + len(Task.objects.all()),
                         'Analytics should be sent when update is called')

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags']['status'], 'realized')


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
@patch.object(InfluxExporter, 'client', fake_client)
class TestTaskMemberAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestTaskMemberAnalytics, self).setUp()
        self.init_projects()

    def test_tags_generation(self, queue_mock):
        user = BlueBottleUserFactory.create()
        task = TaskFactory.create(author=user, people_needed=2)
        task_member = TaskMemberFactory.create(time_spent=10, member=user, task=task, status='applied')

        project = task.project
        expected_tags = {
            'type': 'task_member',
            'tenant': u'test',
            'status': 'applied',
            'location': '',
            'location_group': '',
            'theme': project.theme.name,
            'theme_slug': project.theme.slug,
        }
        expected_fields = {
            'id': task_member.id,
            'task_id': task.id,
            'user_id': user.id,
            'hours': task_member.time_spent
        }

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], expected_tags)
        self.assertEqual(kwargs['fields'], expected_fields)

    def test_unchanged_status(self, queue_mock):
        user = BlueBottleUserFactory.create()
        task_member = TaskMemberFactory.create(member=user, status='applied')
        previous_call_count = queue_mock.call_count

        # Update record without changing status
        task_member.motivation = 'I want an extra clean beach'
        task_member.save()

        self.assertEqual(previous_call_count, queue_mock.call_count,
                         'Analytics should only be sent when status changes')

    def test_status_change(self, queue_mock):
        user = BlueBottleUserFactory.create()
        task = TaskFactory.create(author=user, people_needed=2)
        task_member = TaskMemberFactory.create(member=user, task=task, status='approved')
        previous_call_count = queue_mock.call_count

        # Update record without changing status
        task_member.status = 'realized'
        task_member.save()

        self.assertEqual(previous_call_count+1, queue_mock.call_count,
                         'Analytics should be sent when task member status changes')

    @patch.object(signals, '_', fake_trans)
    def test_theme_translated(self, queue_mock):
        theme = ProjectThemeFactory.create(name='Cleaning the beach',
                                           slug='cleaning-the-beach')
        project = ProjectFactory.create(theme=theme)
        task = TaskFactory.create(project=project)
        task_member = TaskMemberFactory.create(task=task)

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags']['theme'], 'Cleaning the park')

    def test_bulk_status_change(self, queue_mock):
        for i in range(10):
            TaskMemberFactory.create()

        previous_call_count = queue_mock.call_count
        TaskMember.objects.update(status='realized')

        self.assertEqual(queue_mock.call_count, previous_call_count + len(Task.objects.all()),
                         'Analytics should be sent when update is called')

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags']['status'], 'realized')


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
@patch.object(InfluxExporter, 'client', fake_client)
class TestOrderAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestOrderAnalytics, self).setUp()
        self.init_projects()

        with patch('bluebottle.analytics.signals.queue_analytics_record') as mock_queue:
            self.user = BlueBottleUserFactory.create()

    def test_tags_generation(self, queue_mock):
        order = OrderFactory.create(total=Decimal('100.00'), user=self.user)
        expected_tags = {
            'type': 'order',
            'tenant': u'test',
            'status': u'created',
            'total_currency': 'EUR',
            'anonymous': False
        }
        expected_fields = {
            'total': 100.0,
            'user_id': order.user.id,
            'id': order.id
        }

        args, kwargs = queue_mock.call_args_list[0]
        self.assertEqual(kwargs['tags'], expected_tags)
        self.assertEqual(kwargs['fields'], expected_fields)
        self.assertEqual(str(kwargs['fields']['total']), '100.0')

    def test_unchanged_status(self, queue_mock):
        order = OrderFactory.create(total=100)
        previous_call_count = queue_mock.call_count

        # Update record without changing status
        order.type = 'blah'
        order.save()

        self.assertEqual(previous_call_count, queue_mock.call_count,
                         'Analytics should only be sent when status changes')


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
@patch.object(InfluxExporter, 'client', fake_client)
class TestVoteAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestVoteAnalytics, self).setUp()
        self.init_projects()

        self.location = LocationFactory.create()
        with patch('bluebottle.analytics.signals.queue_analytics_record') as mock_queue:
            self.user = BlueBottleUserFactory.create()
            self.project = ProjectFactory.create(location=self.location)

    def test_tags_generation(self, queue_mock):
        vote = VoteFactory.create(project=self.project)
        project = vote.project
        expected_tags = {
            'type': 'vote',
            'tenant': u'test',
            'location': self.location.name,
            'location_group': self.location.group.name,
            'theme': project.theme.name,
            'theme_slug': project.theme.slug

        }
        expected_fields = {
            'id': vote.id,
            'user_id': vote.voter.id,
            'project_id': vote.project.id
        }

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], expected_tags)
        self.assertEqual(kwargs['fields'], expected_fields)


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
@patch.object(InfluxExporter, 'client', fake_client)
class TestWallpostAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestWallpostAnalytics, self).setUp()
        self.init_projects()

    def test_tags_generation(self, queue_mock):
        project = ProjectFactory.create()
        donation = DonationFactory.create(project=project)

        wallpost = TextWallpostFactory.create()
        expected_tags = {
            'type': 'wallpost',
            'tenant': u'test'
        }
        expected_fields = {
            'id': wallpost.id,
            'user_id': wallpost.author.id
        }

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], expected_tags)
        self.assertEqual(kwargs['fields'], expected_fields)

    def test_system_wallpost(self, queue_mock):
        project = ProjectFactory.create()
        donation = DonationFactory.create(project=project)

        previous_call_count = queue_mock.call_count

        SystemWallpostFactory.create(related_object=donation, content_object=project)
        self.assertEqual(queue_mock.call_count, previous_call_count,
                         'Analytics should not be sent for system wallposts')

    def test_reaction(self, queue_mock):
        wallpost = TextWallpostFactory.create()
        reaction = ReactionFactory.create(wallpost=wallpost, author=wallpost.author)

        expected_tags = {
            'type': 'wallpost',
            'sub_type': 'reaction',
            'tenant': u'test'
        }

        expected_fields = {
            'id': reaction.id,
            'user_id': reaction.author.id
        }

        args, kwargs = queue_mock.call_args

        self.assertEqual(kwargs['tags'], expected_tags)
        self.assertEqual(kwargs['fields'], expected_fields)


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
@patch.object(InfluxExporter, 'client', fake_client)
class TestMemberAnalytics(BluebottleTestCase):
    def test_tags_generation(self, queue_mock):
        member = BlueBottleUserFactory.create()
        expected_tags = {
            'type': 'member',
            'tenant': u'test',
            'event': 'signup'
        }
        expected_fields = {
            'user_id': member.id
        }

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], expected_tags)
        self.assertEqual(kwargs['fields'], expected_fields)

    def test_member_update(self, queue_mock):
        member = BlueBottleUserFactory.create()
        previous_call_count = queue_mock.call_count

        member.first_name = 'Bob'
        member.save()
        self.assertEqual(queue_mock.call_count, previous_call_count,
                         'Analytics should not be sent when member updated')
