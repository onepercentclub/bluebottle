from bluebottle.time_based.tests.factories import DateActivityFactory

from bluebottle.time_based.models import DateActivity

from bluebottle.time_based.admin import DateActivityAdmin
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
        self.event_admin = DateActivityAdmin(DateActivity, self.site)

    def test_activity_segment_admin(self):
        activity = DateActivityFactory.create()
        activity_url = reverse('admin:time_based_dateactivity_change', args=(activity.id,))
        response = self.client.get(activity_url)
        self.assertNotContains(response, 'Segment:')
        segment_type = SegmentTypeFactory.create()
        SegmentFactory.create_batch(5, type=segment_type)
        response = self.client.get(activity_url)
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
