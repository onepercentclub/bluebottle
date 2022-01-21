from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from bluebottle.segments.admin import SegmentAdmin
from bluebottle.segments.models import Segment
from bluebottle.segments.tests.factories import SegmentTypeFactory, SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.time_based.admin import DateActivityAdmin
from bluebottle.time_based.models import DateActivity
from bluebottle.time_based.tests.factories import DateActivityFactory


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


class TestMemberSegmentAdmin(BluebottleAdminTestCase):

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super(TestMemberSegmentAdmin, self).setUp()
        self.app.set_user(self.superuser)
        self.site = AdminSite()
        department = SegmentTypeFactory.create(name='department')
        self.engineering = SegmentFactory.create(name='engineering', type=department)
        SegmentFactory.create(name='product', type=department)
        title = SegmentTypeFactory.create(name='title')
        SegmentFactory.create_batch(3, type=title)
        self.member = BlueBottleUserFactory.create()

    def test_member_segments_admin(self):
        activity = DateActivityFactory.create(owner=self.member)
        member_url = reverse('admin:members_member_change', args=(self.member.id,))
        page = self.app.get(member_url)
        form = page.forms['member_form']
        form['department'] = [self.engineering.id]
        form.submit()
        self.member.refresh_from_db()
        self.assertEqual(self.member.segments.first(), self.engineering)
        activity.refresh_from_db()
        self.assertEqual(activity.segments.first(), self.engineering)
