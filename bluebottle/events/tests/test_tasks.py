from datetime import timedelta

from django.core import mail
from django.utils.timezone import now

from bluebottle.events.models import Event
from bluebottle.events.tasks import check_event_end, check_event_start
from bluebottle.events.tests.factories import EventFactory
from bluebottle.events.transitions import EventTransitions
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
        start = now() - timedelta(hours=1)
        event = EventFactory.create(
            initiative=self.initiative,
            start_time=start.time(),
            start_date=start.date(),
            duration=3
        )
        event.review_transitions.submit()
        event.save()
        self.assertEqual(event.status, 'open')
        check_event_start()
        check_event_end()
        event = Event.objects.get(pk=event.pk)
        self.assertEqual(event.status, 'running')

    def test_event_end_task(self):
        user = BlueBottleUserFactory.create(first_name='Nono')
        start = now() - timedelta(hours=5)
        event = EventFactory.create(
            owner=user,
            initiative=self.initiative,
            start_time=start.time(),
            start_date=start.date(),
            duration=1
        )
        event.review_transitions.submit()
        event.transitions.start()
        event.save()

        self.assertEqual(event.status, 'running')
        check_event_start()
        check_event_end()
        event = Event.objects.get(pk=event.pk)
        self.assertEqual(event.status, EventTransitions.values.succeeded)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "The status of your event was changed to successful")
        self.assertTrue("Hi Nono,", mail.outbox[0].body)
