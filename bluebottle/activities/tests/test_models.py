from django.test import TestCase

from bluebottle.events.tests.factories import EventFactory
from bluebottle.segments.tests.factories import SegmentFactory, SegmentTypeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


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
        activity = EventFactory.create(owner=self.user, status='succeeded')
        self.user.segments.remove(self.team)
        self.user.segments.add(self.other_team)

        activity.save()

        self.assertTrue(self.unit in activity.segments.all())
        self.assertTrue(self.team in activity.segments.all())
        self.assertFalse(self.other_team in activity.segments.all())

    def test_segments_already_set_open(self):
        activity = EventFactory.create(owner=self.user, status='open')
        self.user.segments.remove(self.team)
        self.user.segments.add(self.other_team)

        activity.save()

        self.assertTrue(self.unit in activity.segments.all())
        self.assertTrue(self.other_team in activity.segments.all())
        self.assertFalse(self.team in activity.segments.all())

    def test_segments_already_set_draft(self):
        activity = EventFactory.create(owner=self.user, status='draft')
        self.user.segments.remove(self.team)
        self.user.segments.add(self.other_team)

        activity.save()

        self.assertTrue(self.unit in activity.segments.all())
        self.assertTrue(self.other_team in activity.segments.all())
        self.assertFalse(self.team in activity.segments.all())
