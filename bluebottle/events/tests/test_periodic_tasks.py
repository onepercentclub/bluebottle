from datetime import timedelta
from django.core import mail
from django.db import connection
import mock
from django.utils import timezone

from bluebottle.clients.utils import LocalTenant
from bluebottle.events.models import Event
from bluebottle.events.tasks import event_tasks
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
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
        start = timezone.now() + timedelta(days=10, hours=10)
        self.event = EventFactory.create(
            initiative=self.initiative,
            start=start,
            status='open',
            capacity=2,
            duration=8
        )

    def test_event_scheduled_task_expired(self):
        self.assertEqual(self.event.status, 'open')
        tenant = connection.tenant
        with mock.patch.object(timezone, 'now', return_value=(timezone.now() + timedelta(days=13))):
            event_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            self.event.refresh_from_db()
        event = Event.objects.get(pk=self.event.pk)
        self.assertEqual(event.status, 'cancelled')

    def test_event_scheduled_task_succeed(self):
        ParticipantFactory.create_batch(2, activity=self.event)
        self.assertEqual(self.event.status, 'full')
        tenant = connection.tenant
        mail.outbox = []
        with mock.patch.object(timezone, 'now', return_value=(timezone.now() + timedelta(days=13))):
            event_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            self.event.refresh_from_db()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.event.status, 'succeeded')

    def test_event_scheduled_task_start(self):
        ParticipantFactory.create_batch(2, activity=self.event)
        self.assertEqual(self.event.status, 'full')
        tenant = connection.tenant
        with mock.patch.object(timezone, 'now', return_value=(timezone.now() + timedelta(days=10, hours=12))):
            event_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            self.event.refresh_from_db()
        event = Event.objects.get(pk=self.event.pk)
        self.assertEqual(event.status, 'running')

    def test_event_scheduled_task_expire(self):
        tenant = connection.tenant
        with mock.patch.object(timezone, 'now', return_value=(timezone.now() + timedelta(days=10, hours=12))):
            event_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            self.event.refresh_from_db()
        event = Event.objects.get(pk=self.event.pk)
        self.assertEqual(event.status, 'cancelled')

    def test_event_scheduled_task_reminder(self):
        ParticipantFactory.create_batch(2, activity=self.event)
        tenant = connection.tenant
        mail.outbox = []
        with mock.patch.object(timezone, 'now', return_value=(timezone.now() + timedelta(days=7))):
            event_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            self.event.refresh_from_db()
        event = Event.objects.get(pk=self.event.pk)
        self.assertEqual(event.status, 'full')
        self.assertEqual(len(mail.outbox), 2)
