from datetime import timedelta

from django.utils.timezone import now

from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class EventTestCase(BluebottleTestCase):

    def test_event_properties(self):
        start = now() - timedelta(hours=1)
        event = EventFactory.create(
            title='The greatest event',
            start_date=start.date(),
            start_time=start.time(),
            duration=3,
            capacity=10
        )

        ParticipantFactory.create_batch(3, activity=event, status='new')
        self.assertEqual(event.participants.count(), 3)

    def test_absolute_url(self):
        activity = EventFactory()
        expected = 'http://testserver/en/initiatives/activities/' \
                   'details/event/{}/{}'.format(activity.id, activity.slug)
        self.assertEqual(activity.get_absolute_url(), expected)

    def test_full(self):
        start = now() + timedelta(hours=1)
        event = EventFactory.create(
            title='The greatest event',
            start_date=start.date(),
            start_time=start.time(),
            duration=1,
            capacity=10,
            initiative=InitiativeFactory.create(status='approved')
        )
        event.review_transitions.submit()

        ParticipantFactory.create_batch(10, activity=event, status='new')
        self.assertEqual(event.status, 'full')

    def test_no_capacity(self):
        start = now() + timedelta(hours=1)
        event = EventFactory.create(
            title='The greatest event',
            start_date=start.date(),
            start_time=start.time(),
            duration=3,
            initiative=InitiativeFactory.create(status='approved'),
            capacity=None
        )
        event.review_transitions.submit()

        ParticipantFactory.create(activity=event, status='new')
        self.assertEqual(event.status, 'open')

    def test_slug(self):
        initiative = EventFactory(title='Test Title')
        self.assertEqual(
            initiative.slug, 'test-title'
        )

    def test_slug_empty(self):
        initiative = EventFactory(title='')
        self.assertEqual(
            initiative.slug, 'new'
        )

    def test_slug_special_characters(self):
        initiative = EventFactory(title='!!! $$$$')
        self.assertEqual(
            initiative.slug, 'new'
        )
