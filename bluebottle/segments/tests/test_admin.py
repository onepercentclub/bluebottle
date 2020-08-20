from bluebottle.events.tests.factories import EventFactory

from bluebottle.events.models import Event

from bluebottle.events.admin import EventAdmin
from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from bluebottle.segments.admin import SegmentAdmin
from bluebottle.segments.models import Segment
from bluebottle.segments.tests.factories import SegmentTypeFactory, SegmentFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class TestSegmentAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestSegmentAdmin, self).setUp()
        self.client.force_login(self.superuser)
        self.site = AdminSite()
        self.segment_admin = SegmentAdmin(Segment, self.site)
        self.event_admin = EventAdmin(Event, self.site)

    def test_activity_segment_admin(self):
        event = EventFactory.create()
        event_url = reverse('admin:events_event_change', args=(event.id,))
        response = self.client.get(event_url)
        self.assertNotContains(response, 'Segment:')
        segment_type = SegmentTypeFactory.create()
        SegmentFactory.create_batch(5, type=segment_type)
        response = self.client.get(event_url)
        self.assertContains(response, 'Segment:')

    def test_segment_admin(self):
        segment_type = SegmentTypeFactory.create()
        SegmentFactory.create_batch(5, type=segment_type)

        segment_url = reverse('admin:segments_segmenttype_change', args=(segment_type.id,))
        response = self.client.get(segment_url)
        self.assertContains(response, 'Segment')

        list_url = reverse('admin:segments_segmenttype_changelist')
        response = self.client.get(list_url)
        self.assertContains(response, 'Number of segments')
