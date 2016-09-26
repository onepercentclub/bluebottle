from mock import patch

from bluebottle.test.utils import BluebottleTestCase
from django.test.utils import override_settings
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectThemeFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory 
from bluebottle.test.factory_models.orders import OrderFactory 
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory 
from bluebottle.test.factory_models.votes import VoteFactory 
from bluebottle.test.factory_models.wallposts import TextWallpostFactory, SystemWallpostFactory 
from bluebottle.test.factory_models.geo import LocationFactory, CountryFactory

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.analytics import signals
from bluebottle.analytics.backends import InfluxExporter

from .common import FakeInfluxDBClient


def fake_trans(str):
    if str == 'Cleaning the beach':
        return 'Cleaning the park'
    return str

def fake_process(self, timestamp, tags={}, fields={}):
    pass


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
            'type': 'project',
            'sub_type': None,
            'tenant': u'test',
        }
        self.expected_fields = {}

    def test_country_tag(self, queue_mock):
        ProjectFactory.create(theme=self.theme, status=self.status,
                              country=self.country)

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], self.expected_tags)

    def test_location_country_tag(self, queue_mock):
        location = LocationFactory.create()
        ProjectFactory.create(theme=self.theme, status=self.status,
                              location=location, country=None)

        self.expected_tags['country'] = location.country.name
        self.expected_tags['location'] = location.name
        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], self.expected_tags)

    def test_tags_generation(self, queue_mock):
        ProjectFactory.create(theme=self.theme, status=self.status,
                              country=self.country)

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
        self.assertEqual(kwargs['fields'], self.expected_fields)

    def test_unchanged_status(self, queue_mock):
        project = ProjectFactory.create(theme=self.theme, status=self.status,
                                        country=self.country)
        previous_call_count = queue_mock.call_count

        # Update record without changing status
        project.title = 'A new title'
        project.save()

        self.assertEqual(previous_call_count, queue_mock.call_count,
                         'Analytics should only be sent when status changes') 


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
@patch.object(InfluxExporter, 'client', fake_client)
class TestTaskAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestTaskAnalytics, self).setUp()
        self.init_projects()

    def test_tags_generation(self, queue_mock):
        user = BlueBottleUserFactory.create()
        TaskFactory.create(author=user)
        expected_tags = {
            'type': 'task',
            'tenant': u'test',
            'status': 'open'
        }
        expected_fields = {}
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


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
@patch.object(InfluxExporter, 'client', fake_client)
class TestTaskMemberAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestTaskMemberAnalytics, self).setUp()
        self.init_projects()

    def test_tags_generation(self, queue_mock):
        user = BlueBottleUserFactory.create()
        expected_tags = {
            'type': 'task_member',
            'tenant': u'test',
            'status': 'applied'
        }
        expected_fields = {}

        task = TaskFactory.create(author=user, people_needed=2)
        TaskMemberFactory.create(member=user, task=task, status='applied')

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], expected_tags)
        self.assertEqual(kwargs['fields'], expected_fields)

    def test_unchanged_status(self, queue_mock):
        user = BlueBottleUserFactory.create()
        task_member = TaskMemberFactory.create(member=user)
        previous_call_count = queue_mock.call_count

        # Update record without changing status
        task_member.motivation = 'I want an extra clean beach'
        task_member.save()

        self.assertEqual(previous_call_count, queue_mock.call_count,
                         'Analytics should only be sent when status changes')


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
@patch.object(InfluxExporter, 'client', fake_client)
class TestOrderAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestOrderAnalytics, self).setUp()

    def test_tags_generation(self, queue_mock):
        order = OrderFactory.create(total=100)
        expected_tags = {
            'type': 'order',
            'tenant': u'test',
            'status': u'created',
            'anonymous': False
        }
        expected_fields = {
            'amount': order.total,
            'id': order.id
        }

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], expected_tags)
        self.assertEqual(kwargs['fields'], expected_fields)

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

    def test_tags_generation(self, queue_mock):
        vote = VoteFactory.create()
        expected_tags = {
            'type': 'vote', 
            'tenant': u'test'
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
