from datetime import timedelta

from django.utils.timezone import now

from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.test.utils import BluebottleTestCase


class EventTestCase(BluebottleTestCase):

    def test_event_properties(self):
        event = EventFactory.create(
            title='The greatest event',
            start_time=now() - timedelta(hours=1),
            end_time=now() + timedelta(hours=3),
            capacity=10
        )

        ParticipantFactory.create_batch(3, activity=event, status='going')

        self.assertEqual(event.duration, 240)
        self.assertEqual(event.participants.count(), 3)
