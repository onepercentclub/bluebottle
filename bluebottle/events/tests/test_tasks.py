from datetime import timedelta

from django.utils.timezone import now

from bluebottle.events.models import Event
from bluebottle.events.tasks import check_event_end, check_event_start
from bluebottle.events.tests.factories import EventFactory
from bluebottle.initiatives.tests.factories import InitiativePlatformSettingsFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class EventTasksTestCase(BluebottleTestCase):

    def setUp(self):
        super(EventTasksTestCase, self).setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=['event']
        )
        self.client = JSONAPITestClient()

    def test_event_start_task(self):
        event = EventFactory.create(
            start_time=now() - timedelta(hours=1),
            end_time=now() + timedelta(hours=3),
        )
        self.assertEqual(event.status, 'open')
        check_event_start()
        check_event_end()
        event = Event.objects.get(pk=event.pk)
        self.assertEqual(event.status, 'running')

    def test_event_end_task(self):
        event = EventFactory.create(
            start_time=now() - timedelta(hours=5),
            end_time=now() - timedelta(hours=1)
        )
        event.start()
        event.save()
        self.assertEqual(event.status, 'running')
        check_event_start()
        check_event_end()
        event = Event.objects.get(pk=event.pk)
        self.assertEqual(event.status, 'done')
