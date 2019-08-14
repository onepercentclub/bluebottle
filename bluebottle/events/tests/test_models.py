from datetime import timedelta

from django.utils.timezone import now

from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class EventTestCase(BluebottleTestCase):

    def test_event_properties(self):
        event = EventFactory.create(
            title='The greatest event',
            start_time=now() - timedelta(hours=1),
            end_time=now() + timedelta(hours=3),
            capacity=10
        )

        ParticipantFactory.create_batch(3, activity=event, status='new')
        self.assertEqual(event.duration, 240)
        self.assertEqual(event.participants.count(), 3)

    def test_absolute_url(self):
        activity = EventFactory()
        expected = 'http://testserver/en/initiatives/activities/event/{}/{}'.format(activity.id, activity.slug)
        self.assertEqual(activity.get_absolute_url(), expected)

    def test_full(self):
        event = EventFactory.create(
            title='The greatest event',
            start_time=now() + timedelta(hours=1),
            end_time=now() + timedelta(hours=1),
            capacity=10,
            initiative=InitiativeFactory.create(status='approved')
        )

        ParticipantFactory.create_batch(10, activity=event, status='new')
        self.assertEqual(event.status, 'full')

    def test_no_capacity(self):
        event = EventFactory.create(
            title='The greatest event',
            start_time=now() + timedelta(hours=1),
            end_time=now() + timedelta(hours=3),
            initiative=InitiativeFactory.create(status='approved'),
            capacity=None
        )

        ParticipantFactory.create(activity=event, status='new')
        self.assertEqual(event.status, 'open')
