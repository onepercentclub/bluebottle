from mock import patch

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.projects import (ProjectFactory, ProjectPhaseFactory, 
                                                     ProjectThemeFactory)
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory 
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.analytics import signals


def fake_trans(str):
    if str == 'Cleaning the beach':
        return 'Cleaning the park'
    return str


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

    def test_tags_generation(self, queue_mock):
        ProjectFactory.create(theme=self.theme, status=self.status)

        queue_mock.assert_called_once_with(tags=self.expected_tags) 

    @patch.object(signals, '_', fake_trans)
    def test_tags_translated(self, queue_mock):
        ProjectFactory.create(theme=self.theme, status=self.status)

        # Simple translation added via fake_trans method above
        self.expected_tags['theme'] = 'Cleaning the park'
        queue_mock.assert_called_once_with(tags=self.expected_tags)

    def test_unchanged_status(self, queue_mock):
        project = ProjectFactory.create(theme=self.theme, status=self.status)

        # Update record without changing status
        project.title = 'A new title'
        project.save()

        self.assertEqual(queue_mock.call_count, 1,
                         'Analytics should only be sent when status changes') 


@patch.object(signals, 'queue_analytics_record')
class TestTaskAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestTaskAnalytics, self).setUp()
        self.init_projects()

        self.user = BlueBottleUserFactory.create()
        self.expected_tags = {
            'type': 'task',
            'tenant': u'test',
            'status': 'open'
        }

    def test_tags_generation(self, queue_mock):
        TaskFactory.create(author=self.user)

        queue_mock.assert_called_once_with(tags=self.expected_tags)

    def test_unchanged_status(self, queue_mock):
        task = TaskFactory.create(author=self.user)

        # Update record without changing status
        task.title = 'Let it be white as snow!'
        task.save()

        self.assertEqual(queue_mock.call_count, 1,
                         'Analytics should only be sent when status changes') 


@patch.object(signals, 'queue_analytics_record')
class TestTaskMemberAnalytics(BluebottleTestCase):
    def setUp(self):
        super(TestTaskMemberAnalytics, self).setUp()
        self.init_projects()

        self.user = BlueBottleUserFactory.create()
        self.expected_tags = {
            'type': 'task_member',
            'tenant': u'test',
            'status': 'applied'
        }

    def test_tags_generation(self, queue_mock):
        TaskMemberFactory.create(member=self.user)

        queue_mock.assert_called_once_with(tags=self.expected_tags)

    def test_unchanged_status(self, queue_mock):
        task_member = TaskMemberFactory.create(member=self.user)

        # Update record without changing status
        task_member.motivation = 'I want an extra clean beach'
        task_member.save()

        self.assertEqual(queue_mock.call_count, 1,
                         'Analytics should only be sent when status changes') 