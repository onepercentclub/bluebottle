from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now

from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.segments.tests.factories import SegmentFactory, SegmentTypeFactory


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


class ActivitySegmentsTestCase(TestCase):
    def setUp(self):

        team_type = SegmentTypeFactory.create(name='Team')
        self.team = SegmentFactory.create(name='Online Marketing', type=team_type)
        self.other_team = SegmentFactory.create(name='Direct Marketing', type=team_type)

        unit_type = SegmentTypeFactory.create(name='Unit')
        self.unit = SegmentFactory.create(name='Marketing', type=unit_type)
        SegmentFactory.create(name='Communications', type=unit_type)

        self.user = BlueBottleUserFactory()
        self.user.segments.add(self.team)
        self.user.segments.add(self.unit)

        super(ActivitySegmentsTestCase, self).setUp()

    def test_segments(self):
        activity = EventFactory.create(owner=self.user)
        self.assertTrue(self.unit in activity.segments.all())
        self.assertTrue(self.team in activity.segments.all())

    def test_segments_already_set(self):
        activity = EventFactory.create(owner=self.user)
        self.user.segments.remove(self.team)
        self.user.segments.add(self.other_team)

        activity.save()

        self.assertTrue(self.unit in activity.segments.all())
        self.assertTrue(self.team in activity.segments.all())
        self.assertFalse(self.other_team in activity.segments.all())
