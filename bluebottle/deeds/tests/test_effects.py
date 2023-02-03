from datetime import date, timedelta

from django.utils.timezone import get_current_timezone

from bluebottle.deeds.effects import RescheduleEffortsEffect
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class CreateEffortContributionTestCase(BluebottleTestCase):
    def setUp(self):
        self.activity = DeedFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            start=date.today() - timedelta(days=10),
            end=date.today() - timedelta(days=20),
        )

        self.tz = get_current_timezone()

    def test_create(self):
        participant = DeedParticipantFactory.create(
            activity=self.activity,
        )

        self.assertEqual(
            participant.contributions.first().start.date(),
            self.activity.end
        )

        self.assertIsNone(
            participant.contributions.first().end
        )

    def test_create_no_end(self):
        self.activity.end = None
        self.activity.save()

        participant = DeedParticipantFactory.create(activity=self.activity)

        self.assertEqual(
            participant.contributions.first().start.date(),
            participant.created.date()
        )

        self.assertIsNone(
            participant.contributions.first().end
        )

    def test_create_no_start(self):
        self.activity.start = None
        self.activity.save()

        participant = DeedParticipantFactory.create(activity=self.activity)

        self.assertEqual(
            participant.contributions.first().start.date(),
            participant.created.date()
        )

        self.assertIsNone(
            participant.contributions.first().end
        )

    def test_create_future_start(self):
        self.activity.start = date.today() + timedelta(days=10)
        self.activity.end = None
        self.activity.save()

        participant = DeedParticipantFactory.create(activity=self.activity)

        self.assertEqual(
            participant.contributions.first().start.date(),
            participant.activity.start
        )

        self.assertIsNone(
            participant.contributions.first().end
        )


class RescheduleEffortsEffectsTestCase(BluebottleTestCase):
    def setUp(self):
        self.activity = DeedFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            start=date.today() - timedelta(days=10),
            end=date.today() - timedelta(days=20),
        )
        self.effect = RescheduleEffortsEffect(self.activity)

        self.participant = DeedParticipantFactory.create(activity=self.activity)
        self.tz = get_current_timezone()

    def test_reschedule_start(self):
        self.activity.start = date.today() + timedelta(days=1)
        self.effect.post_save()

        self.assertEqual(
            self.participant.contributions.first().start.astimezone(self.tz).date(),
            self.activity.start
        )

    def test_unset_start(self):
        current_start = self.participant.contributions.first().start
        self.activity.start = None
        self.effect.post_save()

        self.assertEqual(
            self.participant.contributions.first().start.date(),
            current_start.date()
        )
