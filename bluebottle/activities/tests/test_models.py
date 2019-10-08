from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now

from bluebottle.events.tests.factories import EventFactory, ParticipantFactory


class ContributionTestCase(TestCase):
    def test_contribution_status_date_changes(self):
        event = EventFactory.create(status='succeeded')
        contribution = ParticipantFactory.create(status='new', activity=event)
        contribution.transitions.succeed()

        self.assertEqual(contribution.status, 'succeeded')
        self.assertAlmostEqual(
            contribution.transition_date, now(), delta=timedelta(seconds=1)
        )

    def test_activitystatus_date_changes(self):
        event = EventFactory.create(status='succeeded')
        event.transitions.close()

        self.assertEqual(event.status, 'closed')
        self.assertAlmostEqual(
            event.transition_date, now(), delta=timedelta(seconds=1)
        )
