from datetime import timedelta
import mock

from django.core import mail
from django.db import connection
from django.utils import timezone

from bluebottle.clients.utils import LocalTenant
from bluebottle.events.models import Event
from bluebottle.events.tasks import event_tasks
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.events.states import EventStateMachine
from bluebottle.initiatives.tests.factories import (
    InitiativePlatformSettingsFactory, InitiativeFactory
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class EventTasksTestCase(BluebottleTestCase):

    def setUp(self):
        super(EventTasksTestCase, self).setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=['event']
        )
        self.client = JSONAPITestClient()
        self.initiative = InitiativeFactory.create(status='approved')
        self.initiative.save()

    def test_event_start_task(self):
        start = timezone.now() + timedelta(hours=1)
        event = EventFactory.create(
            initiative=self.initiative,
            start=start,
            duration=3
        )
        event.states.submit(save=True)

        ParticipantFactory.create(activity=event)

        self.assertEqual(event.status, 'open')
        tenant = connection.tenant
        future = timezone.now() + timedelta(hours=2)
        with mock.patch.object(timezone, 'now', return_value=future):
            event_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            event = Event.objects.get(pk=event.pk)
        self.assertEqual(event.status, 'running')

    def test_event_start_task_no_participants(self):
        start = timezone.now() + timedelta(hours=1)
        event = EventFactory.create(
            initiative=self.initiative,
            start=start,
            duration=3
        )
        event.states.submit(save=True)

        self.assertEqual(event.status, 'open')
        tenant = connection.tenant
        future = timezone.now() + timedelta(hours=4)
        with mock.patch.object(timezone, 'now', return_value=future):
            event_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            event = Event.objects.get(pk=event.pk)
        self.assertEqual(event.status, 'cancelled')

    def test_event_end_task(self):
        user = BlueBottleUserFactory.create(first_name='Nono')
        start = timezone.now() + timedelta(hours=5)
        event = EventFactory.create(
            owner=user,
            initiative=self.initiative,
            title='Finish them translations, Rolfertjan!',
            start=start,
            duration=1
        )
        event.states.submit(save=True)
        ParticipantFactory.create_batch(3, activity=event)

        tenant = connection.tenant

        mail.outbox = []

        future = timezone.now() + timedelta(hours=6)
        with mock.patch.object(timezone, 'now', return_value=future):
            event_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            event = Event.objects.get(pk=event.pk)
        self.assertEqual(event.status, EventStateMachine.succeeded.value)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, u'Your event "{}" took place! \U0001f389'.format(event.title))
        self.assertTrue("Hi Nono,", mail.outbox[0].body)

    def test_event_reminder_task(self):
        user = BlueBottleUserFactory.create(first_name='Nono')
        start = timezone.now() + timedelta(days=4)
        event = EventFactory.create(
            owner=user,
            status='open',
            initiative=self.initiative,
            start=start,
            duration=1
        )

        ParticipantFactory.create_batch(3, activity=event, status='new')
        ParticipantFactory.create(activity=event, status='withdrawn')

        tenant = connection.tenant
        event_tasks()

        recipients = [message.to[0] for message in mail.outbox]

        with LocalTenant(tenant, clear_tenant=True):
            event.refresh_from_db()

        for participant in event.intentions.all():
            if participant.status == 'new':
                self.assertTrue(participant.user.email in recipients)
            else:
                self.assertFalse(participant.user.email in recipients)

        recipients = [message.to[0] for message in mail.outbox]

        for participant in event.intentions.all():
            if participant.status == 'new':
                self.assertTrue(participant.user.email in recipients)
            else:
                self.assertFalse(participant.user.email in recipients)

        mail.outbox = []

    def test_event_reminder_task_twice(self):
        user = BlueBottleUserFactory.create(first_name='Nono')
        start = timezone.now() + timedelta(days=4)
        event = EventFactory.create(
            owner=user,
            status='open',
            initiative=self.initiative,
            start=start,
            duration=1
        )

        ParticipantFactory.create_batch(3, activity=event, status='new')
        ParticipantFactory.create(activity=event, status='withdrawn')

        event_tasks()
        mail.outbox = []
        event_tasks()
        event_tasks()

        self.assertEqual(len(mail.outbox), 0)
