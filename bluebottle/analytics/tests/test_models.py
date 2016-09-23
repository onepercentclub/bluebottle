from mock import patch

from bluebottle.test.utils import BluebottleTestCase
from django.test.utils import override_settings
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectThemeFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory 
from bluebottle.test.factory_models.orders import OrderFactory 
from bluebottle.test.factory_models.donations import DonationFactory 
from bluebottle.test.factory_models.votes import VoteFactory 
from bluebottle.test.factory_models.wallposts import TextWallpostFactory, SystemWallpostFactory 
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.analytics import signals


def fake_trans(str):
    if str == 'Cleaning the beach':
        return 'Cleaning the park'
    return str


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
class TestProjectAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestProjectAnalytics, self).setUp()
        self.init_projects()

        self.theme = ProjectThemeFactory.create(name='Cleaning the beach',
                                                slug='cleaning-the-beach')
        self.status = ProjectPhase.objects.get(slug='campaign')
        self.expected_tags = {
            'status': self.status.name,
            'theme_slug': 'cleaning-the-beach',
            'status_slug': self.status.slug,
            'country': '',
            'theme': 'Cleaning the beach',
            'location': '',
            'type': 'project',
            'sub_type': None,
            'tenant': u'test',
        }
        self.expected_fields = {}

    def test_tags_generation(self, queue_mock):
        ProjectFactory.create(theme=self.theme, status=self.status)

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], self.expected_tags)
        self.assertEqual(kwargs['fields'], self.expected_fields)

    @patch.object(signals, '_', fake_trans)
    def test_tags_translated(self, queue_mock):
        ProjectFactory.create(theme=self.theme, status=self.status)

        # Simple translation added via fake_trans method above
        self.expected_tags['theme'] = 'Cleaning the park'
        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], self.expected_tags)
        self.assertEqual(kwargs['fields'], self.expected_fields)

    def test_unchanged_status(self, queue_mock):
        project = ProjectFactory.create(theme=self.theme, status=self.status)
        previous_call_count = queue_mock.call_count

        # Update record without changing status
        project.title = 'A new title'
        project.save()

        self.assertEqual(previous_call_count, queue_mock.call_count,
                         'Analytics should only be sent when status changes') 


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
class TestTaskAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestTaskAnalytics, self).setUp()
        self.init_projects()
        self.user = BlueBottleUserFactory.create()

    def test_tags_generation(self, queue_mock):
        TaskFactory.create(author=self.user)
        self.expected_tags = {
            'type': 'task',
            'tenant': u'test',
            'status': 'open'
        }
        self.expected_fields = {}
        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], self.expected_tags)
        self.assertEqual(kwargs['fields'], self.expected_fields)

    def test_unchanged_status(self, queue_mock):
        task = TaskFactory.create(author=self.user) 
        previous_call_count = queue_mock.call_count

        # Update record without changing status
        task.title = 'Let it be white as snow!'
        task.save()

        self.assertEqual(previous_call_count, queue_mock.call_count,
                         'Analytics should only be sent when status changes') 


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
class TestTaskMemberAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestTaskMemberAnalytics, self).setUp()
        self.init_projects()
        self.user = BlueBottleUserFactory.create()

    def test_tags_generation(self, queue_mock):
        self.expected_tags = {
            'type': 'task_member',
            'tenant': u'test',
            'status': 'applied'
        }
        self.expected_fields = {}

        task = TaskFactory.create(author=self.user, people_needed=2)
        TaskMemberFactory.create(member=self.user, task=task, status='applied')

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], self.expected_tags)
        self.assertEqual(kwargs['fields'], self.expected_fields)

    def test_unchanged_status(self, queue_mock):
        task_member = TaskMemberFactory.create(member=self.user)
        previous_call_count = queue_mock.call_count

        # Update record without changing status
        task_member.motivation = 'I want an extra clean beach'
        task_member.save()

        self.assertEqual(previous_call_count, queue_mock.call_count,
                         'Analytics should only be sent when status changes')


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
class TestOrderAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestOrderAnalytics, self).setUp()

    def test_tags_generation(self, queue_mock):
        self.order = OrderFactory.create(total=100)
        self.expected_tags = {
            'type': 'order',
            'tenant': u'test',
            'status': 'created',
            'anonymous': True
        }
        self.expected_fields = {
            'amount': self.order.total,
            'id': self.order.id
        }

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], self.expected_tags)
        self.assertEqual(kwargs['fields'], self.expected_fields)

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
class TestVoteAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestVoteAnalytics, self).setUp()
        self.init_projects()

    def test_tags_generation(self, queue_mock):
        self.vote = VoteFactory.create()
        self.expected_tags = {
            'type': 'vote', 
            'tenant': u'test'
        }
        self.expected_fields = {
            'id': self.vote.id,
            'user_id': self.vote.voter.id,
            'project_id': self.vote.project.id
        }

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], self.expected_tags)
        self.assertEqual(kwargs['fields'], self.expected_fields)


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
class TestWallpostAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestWallpostAnalytics, self).setUp()
        self.init_projects()

    def test_tags_generation(self, queue_mock):
        self.project = ProjectFactory.create()
        self.donation = DonationFactory.create(project=self.project)

        wallpost = TextWallpostFactory.create()
        self.expected_tags = {
            'type': 'wallpost',
            'tenant': u'test'
        }
        self.expected_fields = {
            'id': wallpost.id,
            'user_id': wallpost.author.id
        }

        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags'], self.expected_tags)
        self.assertEqual(kwargs['fields'], self.expected_fields)

    def test_system_wallpost(self, queue_mock):
        self.project = ProjectFactory.create()
        self.donation = DonationFactory.create(project=self.project)

        previous_call_count = queue_mock.call_count

        SystemWallpostFactory.create(related_object=self.donation, content_object=self.project)
        self.assertEqual(queue_mock.call_count, previous_call_count,
                         'Analytics should not be sent for system wallposts')
