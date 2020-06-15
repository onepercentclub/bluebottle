from datetime import timedelta
from django.db import connection
import mock
from django.utils import timezone

from bluebottle.clients.utils import LocalTenant
from bluebottle.events.models import Event
from bluebottle.events.tasks import event_tasks
from bluebottle.events.tests.factories import EventFactory
from bluebottle.initiatives.tests.factories import (
    InitiativeFactory
)
from bluebottle.test.utils import BluebottleTestCase


@mock.patch('bluebottle.events.models.Event.triggers', [])
class EventScheduledTasksTestCase(BluebottleTestCase):

    def setUp(self):
        super(EventScheduledTasksTestCase, self).setUp()
        self.initiative = InitiativeFactory.create(status='approved')
        self.initiative.save()

    def test_event_start_task(self):
        start = timezone.now() - timedelta(hours=20)
        event = EventFactory.create(
            initiative=self.initiative,
            start=start,
            status='open',
            duration=8
        )
        self.assertEqual(event.status, 'open')
        tenant = connection.tenant
        event_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            event.refresh_from_db()
        event = Event.objects.get(pk=event.pk)
        self.assertEqual(event.status, 'closed')
