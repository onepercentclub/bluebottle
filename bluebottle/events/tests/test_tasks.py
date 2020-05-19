from datetime import timedelta
import mock

from django.core import mail
from django.db import connection
from django.utils import timezone

from bluebottle.clients.utils import LocalTenant
from bluebottle.events.models import Event
from bluebottle.events.tasks import check_event_end, check_event_start, check_event_reminder
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
        start = timezone.now() - timedelta(hours=1)
        event = EventFactory.create(
            initiative=self.initiative,
            start=start,
            duration=3
        )

        ParticipantFactory.create(activity=event)

        self.assertEqual(event.status, 'open')
        check_event_start()
        check_event_end()
        event = Event.objects.get(pk=event.pk)
        self.assertEqual(event.status, 'running')

    def test_event_start_task_no_participants(self):
        start = timezone.now() - timedelta(hours=1)
        event = EventFactory.create(
            initiative=self.initiative,
            start=start,
            duration=3
        )

        self.assertEqual(event.status, 'open')
        check_event_start()
        check_event_end()
        event = Event.objects.get(pk=event.pk)
        self.assertEqual(event.status, 'open')

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
        ParticipantFactory.create_batch(3, activity=event)

        tenant = connection.tenant

        future = timezone.now() + timedelta(hours=6)

        with mock.patch.object(timezone, 'now', return_value=future):
            check_event_start()
            check_event_end()

        with LocalTenant(tenant, clear_tenant=True):
            event = Event.objects.get(pk=event.pk)
        self.assertEqual(event.status, EventStateMachine.succeeded.value)

        self.assertEqual(len(mail.outbox), 10)
        self.assertEqual(mail.outbox[-1].subject, 'You completed your event "{}"!'.format(event.title))
        self.assertTrue("Hi Nono,", mail.outbox[-1].body)

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
        check_event_reminder()

        recipients = [message.to[0] for message in mail.outbox]

        with LocalTenant(tenant, clear_tenant=True):
            event.refresh_from_db()

        for participant in event.contributions.all():
            if participant.status == 'new':
                self.assertTrue(participant.user.email in recipients)
            else:
                self.assertFalse(participant.user.email in recipients)

        recipients = [message.to[0] for message in mail.outbox]

        for participant in event.contributions.all():
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

        check_event_reminder()
        mail.outbox = []
        check_event_reminder()

        self.assertEqual(len(mail.outbox), 0)
