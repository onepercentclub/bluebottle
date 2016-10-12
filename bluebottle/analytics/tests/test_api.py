from mock import patch

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from bluebottle.tasks.models import Task
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.analytics import signals
from bluebottle.analytics.backends import InfluxExporter
from .common import FakeInfluxDBClient

fake_client = FakeInfluxDBClient()


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(signals, 'queue_analytics_record')
@patch.object(InfluxExporter, 'client', fake_client)
class TaskMemberApiAnalyticsTest(BluebottleTestCase):
    def setUp(self):
        super(TaskMemberApiAnalyticsTest, self).setUp()

        self.init_projects()

    def test_taskmember_status_changes(self, queue_mock):
        user = BlueBottleUserFactory.create()
        task = TaskFactory.create(author=user, people_needed=2, status='realized')
        task_member = TaskMemberFactory.create(time_spent=10, member=user, task=task, status='applied')

        task_member_url = reverse('task_member_detail', kwargs={'pk': task_member.id})
        task_member_data = {
            'task': task.id,
            'status': 'realized'
        }
        self.client.put(task_member_url, task_member_data, token="JWT {0}".format(user.get_jwt_token()))
        args, kwargs = queue_mock.call_args
        self.assertEqual(kwargs['tags']['status'], 'realized')
