from datetime import timedelta

from django.core import mail
from django.utils.timezone import now

from bluebottle.events.models import Participant
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class EventTestCase(BluebottleTestCase):

    def test_event_properties(self):

        start = now() - timedelta(hours=1)
        event = EventFactory.create(
            title='The greatest event',
            start=start,
            duration=3,
            capacity=10,
            initiative=InitiativeFactory.create(status='approved')
        )
        event.states.submit(save=True)

        ParticipantFactory.create_batch(3, activity=event, status='new')
        self.assertEqual(event.participants.count(), 3)

    def test_absolute_url(self):
        activity = EventFactory()
        expected = 'http://testserver/en/initiatives/activities/' \
                   'details/event/{}/{}'.format(activity.id, activity.slug)
        self.assertEqual(activity.get_absolute_url(), expected)

    def test_full(self):
        start = now() + timedelta(hours=2)
        event = EventFactory.create(
            title='The greatest event',
            start=start,
            duration=1,
            capacity=10,
            initiative=InitiativeFactory.create(status='approved')
        )
        event.states.submit(save=True)

        ParticipantFactory.create_batch(event.capacity, activity=event)
        event.refresh_from_db()

        self.assertEqual(event.status, 'full')

    def test_reopen_changed_capacity(self):
        start = now() + timedelta(hours=2)
        event = EventFactory.create(
            title='The greatest event',
            start=start,
            duration=1,
            capacity=10,
            initiative=InitiativeFactory.create(status='approved')
        )
        event.states.submit(save=True)

        ParticipantFactory.create_batch(event.capacity, activity=event)

        event.refresh_from_db()
        self.assertEqual(event.status, 'full')

        event.capacity = 20
        event.save()

        self.assertEqual(event.status, 'open')

    def test_reopen_delete_participant(self):
        start = now() + timedelta(hours=2)
        event = EventFactory.create(
            title='The greatest event',
            start=start,
            duration=1,
            capacity=10,
            initiative=InitiativeFactory.create(status='approved')
        )
        event.states.submit(save=True)

        ParticipantFactory.create_batch(10, activity=event)

        event.refresh_from_db()
        self.assertEqual(event.status, 'full')

        event.participants[0].delete()

        event.refresh_from_db()
        self.assertEqual(event.status, 'open')

    def test_no_capacity(self):
        start = now() + timedelta(hours=1)
        event = EventFactory.create(
            title='The greatest event',
            start=start,
            duration=3,
            initiative=InitiativeFactory.create(status='approved'),
            capacity=None
        )

        event.states.submit(save=True)

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

    def test_date_changed(self):
        event = EventFactory(
            title='Test Title',
            status='open',
            start=now() + timedelta(days=4),
        )

        ParticipantFactory.create_batch(3, activity=event, status='new')
        ParticipantFactory.create(activity=event, status='withdrawn')

        mail.outbox = []

        event.start = event.start + timedelta(days=1)
        event.save()

        recipients = [message.to[0] for message in mail.outbox]

        for participant in event.contributions.instance_of(Participant):
            if participant.status == 'new':
                self.assertTrue(participant.user.email in recipients)
            else:
                self.assertFalse(participant.user.email in recipients)

    def test_date_not_changed(self):
        event = EventFactory(
            title='Test Title',
            status='open',
            start=now() + timedelta(days=4),
        )
        ParticipantFactory.create_batch(3, activity=event, status='new')
        ParticipantFactory.create(activity=event, status='withdrawn')

        mail.outbox = []

        event.title = 'New title'
        event.save()

        self.assertEqual(len(mail.outbox), 0)
