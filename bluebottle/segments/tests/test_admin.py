import re

from django.contrib.admin.sites import AdminSite
from django.db import connection, reset_queries
from django.test.utils import override_settings
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

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super(TestSegmentAdmin, self).setUp()
        self.app.set_user(self.superuser)
        self.client.force_login(self.superuser)
        self.site = AdminSite()
        self.segment_admin = SegmentAdmin(Segment, self.site)
        self.event_admin = DateActivityAdmin(DateActivity, self.site)

    def test_activity_segment_admin(self):
        activity = DateActivityFactory.create()
        activity_url = reverse('admin:time_based_dateactivity_change', args=(activity.id,))
        response = self.client.get(activity_url)
        self.assertNotContains(response, 'Department:')
        segment_type = SegmentTypeFactory.create(name="Department")
        SegmentFactory.create_batch(5, segment_type=segment_type)
        response = self.client.get(activity_url)
        self.assertContains(response, 'Segments')
        self.assertContains(response, 'Department:')

    def test_activity_segment_admin_uses_autocomplete(self):
        segment_type = SegmentTypeFactory.create(name="Department")
        segments = SegmentFactory.create_batch(30, segment_type=segment_type)
        activity = DateActivityFactory.create()
        activity.segments.add(segments[0])

        activity_url = reverse('admin:time_based_dateactivity_change', args=(activity.id,))
        response = self.client.get(activity_url)
        content = response.content.decode()

        self.assertIn('admin-autocomplete', content)
        self.assertIn(f'segment_type={segment_type.id}', content)

        field_name = segment_type.field_name
        match = re.search(
            rf'<select[^>]*name="{re.escape(field_name)}"[^>]*>(.*?)</select>',
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(match, f'Segment select for {field_name} not found')
        select_html = match.group(0)
        self.assertIn('admin-autocomplete', select_html)
        self.assertIn(f'value="{segments[0].id}"', select_html)
        self.assertNotIn(f'value="{segments[1].id}"', select_html)

    def test_segment_autocomplete_filters_by_type(self):
        type_a = SegmentTypeFactory.create(name='Type A')
        type_b = SegmentTypeFactory.create(name='Type B')
        segment_a = SegmentFactory.create(name='SharedName A', segment_type=type_a)
        segment_b = SegmentFactory.create(name='SharedName B', segment_type=type_b)

        url = reverse('admin:autocomplete')
        response = self.client.get(url, {
            'app_label': 'activities',
            'model_name': 'activity',
            'field_name': 'segments',
            'term': 'SharedName',
            'segment_type': type_a.id,
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {result['id'] for result in payload['results']}
        self.assertIn(str(segment_a.id), ids)
        self.assertNotIn(str(segment_b.id), ids)

    def test_segment_admin(self):
        segment_type = SegmentTypeFactory.create(name='Job title')
        SegmentFactory.create_batch(5, segment_type=segment_type)

        segment_url = reverse('admin:segments_segmenttype_change', args=(segment_type.id,))
        response = self.client.get(segment_url)
        self.assertContains(response, 'Segment')

        list_url = reverse('admin:segments_segmenttype_changelist')
        response = self.client.get(list_url)
        self.assertContains(response, 'Number of segments')
        self.assertContains(response, 'Job title')
        self.assertContains(
            response,
            reverse('admin:segments_segmenttype_change', args=(segment_type.id,))
        )

    def test_segment_email_domain(self):
        segment_type = SegmentTypeFactory.create()
        segment = SegmentFactory.create(segment_type=segment_type)
        self.assertEqual(segment.email_domains, ['example.com'])

        segment_url = reverse('admin:segments_segment_change', args=(segment.id, ))
        page = self.app.get(segment_url)

        form = page.forms['segment_form']
        form['name'] = 'My Segment'
        form['email_domains'] = 'test.com, test2.com'
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        segment.refresh_from_db()
        self.assertEqual(segment.email_domains, ['test.com', 'test2.com'])


@override_settings(DEBUG=True)
class ActivityAdminSegmentQueryTest(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def test_change_view_does_not_query_all_segments(self):
        self.client.force_login(self.superuser)
        segment_type = SegmentTypeFactory.create(name="Department")
        segments = SegmentFactory.create_batch(100, segment_type=segment_type)
        activity = DateActivityFactory.create()
        activity.segments.add(segments[0])

        url = reverse("admin:time_based_dateactivity_change", args=(activity.id,))
        self.client.get(url)

        reset_queries()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        segment_queries = [
            q for q in connection.queries
            if "segments_segment" in q["sql"].lower()
            and "segmenttype" not in q["sql"].lower()
            and "segment_manager" not in q["sql"].lower()
        ]
        self.assertLess(len(segment_queries), 10, segment_queries)

        content = response.content.decode()
        self.assertIn("admin-autocomplete", content)
        self.assertNotIn(f'value="{segments[1].id}"', content)


class TestSegmentTypeAdmin(BluebottleAdminTestCase):

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super(TestSegmentTypeAdmin, self).setUp()
        self.app.set_user(self.superuser)
        self.client.force_login(self.superuser)
        self.site = AdminSite()

    def test_required_segment_types_no_segments(self):
        member_settings_url = reverse('admin:members_memberplatformsettings_change')
        page = self.app.get(member_settings_url)
        self.assertFalse('Mark segment types as required' in page.text)
        department = SegmentTypeFactory.create(name='Department')
        hobbies = SegmentTypeFactory.create(name='Hobbies')
        page = self.app.get(member_settings_url)
        self.assertTrue('Required fields' in page.text)
        self.assertTrue('no segment types are marked as required' in page.text)
        page = page.click('segment type overview')
        page = self.app.get(reverse('admin:segments_segmenttype_change', args=(department.id,)))
        form = page.forms[1]
        form['required'].checked = True
        form['name'] = "My segment type"
        page = form.submit().follow()
        page = self.app.get(reverse('admin:segments_segmenttype_change', args=(hobbies.id,)))
        form = page.forms[1]
        form['required'].checked = True
        form['name'] = "Another segment type"
        page = form.submit().follow()
        self.assertTrue(page.forms[1]['form-0-required'].checked)
        self.assertTrue(page.forms[1]['form-1-required'].checked)
        page = self.app.get(member_settings_url)
        self.assertFalse('no segment types are marked as required' in page.text)

    def test_can_save_new_language_without_segment_translations(self):
        """
        Saving a SegmentType translation must not fail when child segments
        only exist in another language (empty required inline names).
        """
        segment_type = SegmentTypeFactory.create(name='Theme', slug='themas')
        segment_type.set_current_language('en')
        segment_type.name = 'Theme'
        segment_type.save()

        segment = SegmentFactory.create(
            segment_type=segment_type,
            name='Loneliness',
            slug='loneliness',
        )
        segment.set_current_language('en')
        segment.name = 'Loneliness'
        segment.save()

        self.assertFalse(segment_type.has_translation('nl'))
        self.assertFalse(segment.has_translation('nl'))

        url = reverse(
            'admin:segments_segmenttype_change',
            args=(segment_type.id,),
        )
        page = self.app.get(url, {'language': 'nl'})
        form = page.forms[1]

        # Inline name is prefilled from the English fallback.
        self.assertEqual(form['segments-0-name'].value, 'Loneliness')

        form['name'] = 'Thema'
        response = form.submit()
        self.assertEqual(response.status_code, 302, response.text)

        segment_type.refresh_from_db()
        self.assertTrue(segment_type.has_translation('nl'))
        segment_type.set_current_language('nl')
        self.assertEqual(segment_type.name, 'Thema')
        # Shared slug must not be overwritten by translated-name prepopulation.
        self.assertEqual(segment_type.slug, 'themas')

        # Unchanged inline names are not written as new translations; parler
        # falls back to the existing English name, which is the intended UX
        # when only translating the segment type label.
        segment.refresh_from_db()
        self.assertFalse(segment.has_translation('nl'))
        self.assertEqual(
            segment.safe_translation_getter('name', language_code='nl', any_language=True),
            'Loneliness',
        )

        segment_type.set_current_language('en')
        self.assertEqual(segment_type.name, 'Theme')
        segment.set_current_language('en')
        self.assertEqual(segment.name, 'Loneliness')

    def test_changing_dutch_leaves_english_unchanged(self):
        """
        Editing Dutch translations must create/update NL only and leave EN as-is.
        """
        segment_type = SegmentTypeFactory.create(name='Theme', slug='themas')
        segment_type.set_current_language('en')
        segment_type.name = 'Theme'
        segment_type.save()

        segment = SegmentFactory.create(
            segment_type=segment_type,
            name='Loneliness',
            slug='loneliness',
        )
        segment.set_current_language('en')
        segment.name = 'Loneliness'
        segment.save()

        url = reverse(
            'admin:segments_segmenttype_change',
            args=(segment_type.id,),
        )
        page = self.app.get(url, {'language': 'nl'})
        form = page.forms[1]

        self.assertEqual(form['segments-0-name'].value, 'Loneliness')

        form['name'] = 'Thema'
        form['segments-0-name'] = 'Eenzaamheid'
        response = form.submit()
        self.assertEqual(response.status_code, 302, response.text)

        segment_type.refresh_from_db()
        segment.refresh_from_db()

        segment_type.set_current_language('nl')
        self.assertEqual(segment_type.name, 'Thema')
        segment.set_current_language('nl')
        self.assertEqual(segment.name, 'Eenzaamheid')

        segment_type.set_current_language('en')
        self.assertEqual(segment_type.name, 'Theme')
        segment.set_current_language('en')
        self.assertEqual(segment.name, 'Loneliness')


class TestMemberSegmentAdmin(BluebottleAdminTestCase):

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super(TestMemberSegmentAdmin, self).setUp()
        self.app.set_user(self.superuser)
        self.site = AdminSite()
        department = SegmentTypeFactory.create(name='department')
        self.engineering = SegmentFactory.create(name='engineering', segment_type=department)
        SegmentFactory.create(name='product', segment_type=department)
        title = SegmentTypeFactory.create(name='title')
        SegmentFactory.create_batch(3, segment_type=title)
        self.member = BlueBottleUserFactory.create()

    def test_member_segments_admin(self):
        activity = DateActivityFactory.create(owner=self.member)
        member_url = reverse('admin:members_member_change', args=(self.member.id,))
        page = self.app.get(member_url)
        form = page.forms['member_form']
        form['segment__department'] = self.engineering.id
        form.submit()
        self.member.refresh_from_db()
        self.assertEqual(self.member.segments.first(), self.engineering)
        activity.refresh_from_db()
        self.assertEqual(activity.segments.first(), self.engineering)

    def test_segment_email_domain(self):
        segment_type = SegmentTypeFactory.create()
        segment = SegmentFactory.create(segment_type=segment_type)

        segment_url = reverse('admin:segments_segment_change', args=(segment.id, ))
        page = self.app.get(segment_url)

        form = page.forms['segment_form']
        form['name'] = 'Name'
        form['email_domains'] = 'test.com, test2.com'
        response = form.submit()
        self.assertEqual(response.status_code, 302)

        segment.refresh_from_db()
        self.assertEqual(segment.email_domains[0], 'test.com')
        self.assertEqual(segment.email_domains[1], 'test2.com')
