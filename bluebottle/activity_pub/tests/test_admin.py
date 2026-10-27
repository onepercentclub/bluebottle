from io import BytesIO

import httmock
import mock
import requests
from django.contrib.admin.sites import AdminSite
from django.contrib.messages import get_messages
from django.core.files import File
from django.urls import reverse

from bluebottle.activity_links.models import (
    LinkedActivity, LinkedCollectCampaign, LinkedDateActivity, LinkedDeadlineActivity,
    LinkedDeed, LinkedFunding, LinkedGrantApplication,
)
from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.admin import FollowerAdmin, FollowingAdminForm, PublishedActivityAdmin
from bluebottle.activity_pub.effects import get_platform_actor
from bluebottle.activity_pub.models import Accept, Follow, Follower, Following, PublishedActivity, Recipient
from bluebottle.activity_pub.tests.factories import (
    CollectCampaignFactory, CreateFactory, CrowdFundingFactory, DoGoodEventFactory,
    GoodDeedFactory, GrantApplicationFactory, OrganizationFactory, SubEventFactory,
)
from bluebottle.activity_pub.tests.test_federated_serializers import image_mock
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.collect.models import CollectActivity
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.deeds.models import Deed
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.funding.models import Funding
from bluebottle.grant_management.models import GrantApplication
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.time_based.models import DateActivity, DeadlineActivity
from bluebottle.time_based.tests.factories import DateActivityFactory


class ActivityPubAdminTestCase(BluebottleAdminTestCase):
    factory = DeedFactory
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()

        self.other_tenant = Client.objects.get(schema_name='test2')
        site_settings = SitePlatformSettings.load()
        with open('./bluebottle/utils/tests/test_images/upload.svg', 'rb') as image:
            site_settings.logo = File(BytesIO(image.read()), name='upload.svg')
            site_settings.share_activities = ['supplier', 'consumer']
            site_settings.save()

        self.country = CountryFactory.create()

        with LocalTenant(self.other_tenant):
            CountryFactory.create(
                alpha2_code=self.country.alpha2_code
            )
            CountryFactory.create()

            site_settings = SitePlatformSettings.load()
            with open('./bluebottle/utils/tests/test_images/upload.svg', 'rb') as image:
                site_settings.logo = File(BytesIO(image.read()), name='upload.svg')
            site_settings.share_activities = ['supplier', 'consumer']
            site_settings.save()

        self.set_platform_activity_types(
            [activity_type for (activity_type, _) in InitiativePlatformSettings.ACTIVITY_TYPES]
        )

        self.app.set_user(self.superuser)
        self.other_platform_url = self.other_tenant.build_absolute_url('/')

    def tearDown(self):
        super().tearDown()

    def create_remote_actor(self):
        return OrganizationFactory.create()

    def create_follower(self, actor=None, accepted=True):
        platform_actor = get_platform_actor()
        if actor is None:
            actor = self.create_remote_actor()
        follow = Follower.objects.create(actor=actor, object=platform_actor)
        if accepted:
            Accept.objects.create(actor=platform_actor, object=follow)
        return follow

    def submit_following_form(self, **kwargs):
        url = reverse('admin:activity_pub_following_add')
        page = self.app.get(url, user=self.superuser)
        form = page.forms['following_form']
        form['platform_url'] = kwargs.get('platform_url', self.other_platform_url)
        form['adoption_type'] = kwargs.get('adoption_type', 'link')
        form['automatic_adoption_activity_types'] = kwargs.get(
            'activity_types', ['deed']
        )
        default_owner = kwargs.get('default_owner')
        if default_owner is not None:
            form['default_owner'] = str(default_owner.id)
        actor = kwargs.get('actor') or self.create_remote_actor()
        with mock.patch(
            'bluebottle.webfinger.client.client.get',
            return_value=self.other_platform_url
        ), mock.patch(
            'bluebottle.activity_pub.adapters.adapter.discover'
        ) as discover:
            discover.side_effect = lambda url: actor
            return form.submit()

    def create_published_activity(self, follow, status='open'):
        activity = DeedFactory.create(status=status)
        adapter.sync(activity)
        publish = activity.activity_pub_model.create_set.first()
        Recipient.objects.create(actor=follow.actor, activity=publish)
        return activity

    def test_following_admin_add_connection_with_link_settings(self):
        default_owner = BlueBottleUserFactory.create()
        self.submit_following_form(
            adoption_type='link',
            activity_types=['deed', 'dateactivity'],
            default_owner=default_owner
        )

        follow = Following.objects.get()
        self.assertEqual(follow.adoption_type, 'link')
        self.assertEqual(
            set(follow.automatic_adoption_activity_types),
            {'deed', 'dateactivity'}
        )
        self.assertEqual(follow.default_owner, default_owner)
        self.assertTrue(follow.object.organization)

    def set_platform_activity_types(self, activity_types):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.activity_types = activity_types
        initiative_settings.save()

    def get_adoption_activity_type_options(self, page):
        return {
            checkbox['value'] for checkbox in page.html.find_all(
                'input', {'name': 'automatic_adoption_activity_types'}
            )
        }

    def test_following_admin_add_only_shows_enabled_activity_types(self):
        self.set_platform_activity_types(['deed', 'dateactivity'])

        page = self.app.get(reverse('admin:activity_pub_following_add'), user=self.superuser)

        self.assertEqual(
            self.get_adoption_activity_type_options(page),
            {'deed', 'dateactivity'}
        )

    def test_following_admin_change_only_shows_enabled_activity_types(self):
        self.set_platform_activity_types(['deed', 'dateactivity'])
        self.submit_following_form(activity_types=['deed'])
        follow = Following.objects.get()

        page = self.app.get(
            reverse('admin:activity_pub_following_change', args=(follow.pk,)),
            user=self.superuser
        )

        self.assertEqual(
            self.get_adoption_activity_type_options(page),
            {'deed', 'dateactivity'}
        )

    def test_following_admin_rejects_disabled_activity_type(self):
        self.set_platform_activity_types(['deed'])
        self.submit_following_form(activity_types=['deed'])
        follow = Following.objects.get()

        form = FollowingAdminForm(
            instance=follow,
            data={
                'automatic_adoption_activity_types': ['funding'],
                'adoption_type': 'link',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('automatic_adoption_activity_types', form.errors)

    def test_following_admin_add_connection_invalid_platform_url(self):
        url = reverse('admin:activity_pub_following_add')
        page = self.app.get(url, user=self.superuser)
        form = page.forms['following_form']
        form['platform_url'] = 'https://invalid.example.com'
        form['adoption_type'] = 'link'
        form['automatic_adoption_activity_types'] = ['deed']

        with mock.patch(
            'bluebottle.activity_pub.admin.client.get',
            side_effect=requests.exceptions.HTTPError()
        ):
            response = form.submit()

        self.assertIn(
            'Could not determine platform information needed for subscribing',
            response.text
        )
        self.assertEqual(Following.objects.count(), 0)

    def test_follower_str_uses_partner_actor(self):
        actor = self.create_remote_actor()
        actor.name = 'DLL'
        actor.save()
        follower = self.create_follower(actor=actor)
        platform_name = str(follower.object)

        self.assertEqual(str(follower), 'DLL')
        self.assertEqual(str(Follow.objects.get(pk=follower.pk)), 'DLL')
        self.assertEqual(str(Follower.objects.get(pk=follower.pk)), 'DLL')
        self.assertNotEqual(str(follower), platform_name)

        url = reverse('admin:activity_pub_follower_change', args=(follower.id,))
        page = self.app.get(url, user=self.superuser)
        breadcrumbs = page.html.find(class_='breadcrumbs')
        self.assertIn('DLL', breadcrumbs.text)
        self.assertNotIn(platform_name, breadcrumbs.text)

    def test_follower_admin_sibling_links_use_follower_change_url(self):
        first = self.create_follower(actor=self.create_remote_actor())
        first.actor.name = 'DLL'
        first.actor.save()
        second = self.create_follower(actor=self.create_remote_actor())
        second.actor.name = 'Do Good Up'
        second.actor.save()

        url = reverse('admin:activity_pub_follower_change', args=(first.id,))
        page = self.app.get(url, user=self.superuser)
        sibling_url = reverse(
            'admin:activity_pub_follower_change', args=(second.id,)
        )
        generic_follow_url = reverse(
            'admin:activity_pub_follow_change', args=(second.id,)
        )

        self.assertIn(sibling_url, page.text)
        self.assertNotIn(generic_follow_url, page.text)
        self.assertIn('Do Good Up', page.text)

    def test_follow_admin_redirects_consumer_to_follower_change(self):
        follower = self.create_follower()
        generic_url = reverse('admin:activity_pub_follow_change', args=(follower.id,))
        expected = reverse('admin:activity_pub_follower_change', args=(follower.id,))

        response = self.app.get(generic_url, user=self.superuser)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, expected)

    def test_follower_admin_publish_activities_button_counts_unpublished(self):
        follower = self.create_follower()

        open_activity = DeedFactory.create(status='open')
        succeeded_activity = DeedFactory.create(status='succeeded')
        running_activity = DateActivityFactory.create(status='running')
        DeedFactory.create(status='draft')
        self.create_published_activity(follower, status='open')

        unpublished_ids = set(
            follower.unpublished_activities.values_list('id', flat=True)
        )
        self.assertEqual(
            unpublished_ids,
            {open_activity.id, succeeded_activity.id, running_activity.id}
        )

        admin = FollowerAdmin(Follower, AdminSite())
        button = admin.publish_activities_button(follower)

        self.assertIn('Publish open activities', button)
        self.assertIn('There are 2 unpublished open activities', button)
        self.assertIn('Publish succeeded activities', button)
        self.assertIn('There is 1 unpublished succeeded activity', button)
        self.assertIn(
            reverse('admin:activity_pub_publish_open_activities', args=(follower.id,)),
            button
        )
        self.assertIn(
            reverse('admin:activity_pub_publish_succeeded_activities', args=(follower.id,)),
            button
        )

    def test_follower_admin_publish_activities_triggers_task(self):
        follower = self.create_follower()
        open_activity = DeedFactory.create(status='open')
        DeedFactory.create(status='succeeded')

        url = reverse('admin:activity_pub_publish_open_activities', args=(follower.id,))
        page = self.app.get(url, user=self.superuser)
        form = page.forms[1]

        with mock.patch('bluebottle.activity_pub.admin.publish_activity.delay_on_commit') as delay:
            response = form.submit(name='confirm')

        self.assertEqual(response.status_code, 302)

        called_actor, called_model, called_tenant = delay.call_args[0]
        self.assertEqual(called_actor, follower.actor)
        self.assertEqual(called_tenant, self.tenant)
        self.assertEqual(
            called_model.pk,
            open_activity.id
        )

    def test_follower_admin_accept_follow_request_sets_publish_mode(self):
        follower = self.create_follower(accepted=False)
        url = reverse('admin:activity_pub_follower_accept', args=(follower.id,))
        page = self.app.get(url, user=self.superuser)
        self.assertContains(page, 'Partner:')
        self.assertContains(page, str(follower.actor))
        self.assertContains(page, 'Adoption type:')
        self.assertContains(page, follower.short_adoption_type)
        form = page.forms[1]
        form['publish_mode'] = 'automatic'
        response = form.submit(name='confirm')

        self.assertEqual(response.status_code, 302)
        follower.refresh_from_db()
        self.assertEqual(follower.publish_mode, 'automatic')
        self.assertTrue(Accept.objects.filter(object=follower).exists())

    def test_shared_activities_adopted_column_counts_accepts(self):
        activity = self.create_published_activity(self.create_follower())
        event = activity.activity_pub_model
        Accept.objects.create(actor=self.create_remote_actor(), object=event)
        Accept.objects.create(actor=self.create_remote_actor(), object=event)

        admin = PublishedActivityAdmin(PublishedActivity, AdminSite())
        self.assertNotIn('adopted', admin.list_display)
        self.assertIsNone(event.adopted)
        self.assertEqual(admin.adopted_count(event), 2)


class EventChildAdminTestMixin:
    factory = None
    factory_kwargs = {}
    adopted_model = None
    linked_model = None
    # Field names that should be rendered as read-only boxes on the change page
    expected_fields = ()

    def setUp(self):
        super().setUp()
        site_settings = SitePlatformSettings.load()
        with open('./bluebottle/utils/tests/test_images/upload.svg', 'rb') as image:
            site_settings.logo = File(BytesIO(image.read()), name='upload.svg')
        site_settings.share_activities = ['supplier', 'consumer']
        site_settings.save()

        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.activity_types = [
            activity_type for (activity_type, _) in InitiativePlatformSettings.ACTIVITY_TYPES
        ]
        initiative_settings.save()

        self.supplier = OrganizationFactory.create(
            iri='http://example.com/organization/supplier',
            name='Supplier platform',
        )
        self.follow = Following.objects.create(
            object=self.supplier,
            adoption_type='sync',
        )

        self.event = self.factory.create(
            iri='http://example.com/event/1',
            organization=self.supplier,
            url='https://example.com/activity/1',
            **self.factory_kwargs
        )
        CreateFactory.create(object=self.event, actor=self.supplier)

        self.app.set_user(self.superuser)
        self.url = reverse(
            f'admin:activity_pub_{self.event._meta.model_name}_change',
            args=(self.event.pk,)
        )
        self.adopt_url = reverse('admin:activity_pub_event_adopt', args=(self.event.pk,))
        self.link_url = reverse('admin:activity_pub_event_link', args=(self.event.pk,))

    def get_field(self, page, name):
        return page.html.find(class_=f'field-{name}')

    def assertFieldContains(self, page, name, value):
        field = self.get_field(page, name)
        self.assertIsNotNone(field, f'Field "{name}" is not shown')
        self.assertIn(str(value), field.text)

    def assertExtraFields(self, page):
        pass

    def assertAdopted(self, activity):
        pass

    def test_change_view_shows_event_data(self):
        page = self.app.get(self.url)
        self.assertEqual(page.status_code, 200)

        for name in self.expected_fields:
            self.assertIsNotNone(self.get_field(page, name), f'Field "{name}" is not shown')

        self.assertFieldContains(page, 'adopt_info', 'Adopting creates a draft.')
        self.assertFieldContains(
            page, 'adopt_info',
            'The other fields are managed by the organisation, and contributions are shared with them.'
        )
        self.assertFieldContains(page, 'name', self.event.name)
        self.assertFieldContains(page, 'display_description', self.event.summary)
        self.assertFieldContains(page, 'source', 'Supplier platform')
        self.assertFieldContains(page, 'url', self.event.url)
        self.assertFieldContains(page, 'iri', self.event.iri)
        self.assertIn(
            self.event.image.url,
            self.get_field(page, 'display_image').find('img')['src']
        )
        self.assertExtraFields(page)

        buttons = page.html.find_all('a', href=self.adopt_url)
        self.assertTrue(buttons)
        for button in buttons:
            self.assertEqual(button.text.strip(), 'Adopt activity')

    def test_adopt_event(self):
        page = self.app.get(self.url)
        with httmock.HTTMock(image_mock):
            response = page.click(href=self.adopt_url, index=0)

        self.event.refresh_from_db()
        activity = self.event.adopted
        self.assertIsNotNone(activity)
        self.assertEqual(
            response.location,
            reverse('admin:activities_activity_change', args=(activity.pk,))
        )
        self.assertTrue(isinstance(activity.get_real_instance(), self.adopted_model))
        self.assertEqual(activity.title, self.event.name)
        self.assertEqual(activity.owner, self.superuser)
        self.assertAdopted(activity.get_real_instance())

        page = self.app.get(self.url)
        self.assertIn('View adopted activity', page.text)
        self.assertIn(
            reverse('admin:activities_activity_change', args=(activity.pk,)),
            page.text
        )
        self.assertNotIn(self.adopt_url, page.text)

    def test_adopt_event_twice(self):
        self.client.force_login(self.superuser)
        with httmock.HTTMock(image_mock):
            self.client.get(self.adopt_url)
            response = self.client.get(self.adopt_url)

        self.assertEqual(
            response.url,
            reverse('admin:activity_pub_event_change', args=(self.event.pk,))
        )
        self.assertEqual(
            str(list(get_messages(response.wsgi_request))[-1]),
            'This event has already been adopted.'
        )
        self.assertEqual(self.adopted_model.objects.count(), 1)

    def test_link_event(self):
        Following.objects.filter(pk=self.follow.pk).update(adoption_type='link')

        page = self.app.get(self.url)
        self.assertFieldContains(
            page, 'adopt_info', 'Linking shows this activity on your platform straight away.'
        )
        self.assertFieldContains(
            page, 'adopt_info', 'People contribute on the organisation’s platform.'
        )
        self.assertNotIn('Adopting creates a draft.', self.get_field(page, 'adopt_info').text)
        self.assertNotIn(self.adopt_url, page.text)
        buttons = page.html.find_all('a', href=self.link_url)
        self.assertTrue(buttons)
        for button in buttons:
            self.assertEqual(button.text.strip(), 'Link activity')

        with httmock.HTTMock(image_mock):
            response = page.click(href=self.link_url, index=0)

        self.event.refresh_from_db()
        linked = self.event.link
        self.assertIsNotNone(linked)
        self.assertEqual(
            response.location,
            reverse('admin:activity_links_linkedactivity_change', args=(linked.pk,))
        )
        self.assertTrue(isinstance(linked.get_real_instance(), self.linked_model))
        self.assertEqual(linked.title, self.event.name)
        self.assertEqual(linked.link, self.event.url)

        self.assertIsNone(self.event.adopted)
        self.assertEqual(self.adopted_model.objects.count(), 0)
        self.assertEqual(LinkedActivity.objects.count(), 1)


class GoodDeedAdminTestCase(EventChildAdminTestMixin, BluebottleAdminTestCase):
    factory = GoodDeedFactory
    adopted_model = Deed
    linked_model = LinkedDeed
    expected_fields = (
        'name', 'display_description', 'display_image', 'source', 'activity', 'url',
        'video_url', 'iri', 'start_time', 'end_time', 'contributor_count',
    )


class CrowdFundingAdminTestCase(EventChildAdminTestMixin, BluebottleAdminTestCase):
    factory = CrowdFundingFactory
    adopted_model = Funding
    linked_model = LinkedFunding
    expected_fields = (
        'name', 'display_description', 'display_image', 'source', 'activity', 'url',
        'video_url', 'iri', 'end_time', 'target', 'donated', 'location',
    )

    def assertExtraFields(self, page):
        self.assertFieldContains(page, 'target', '5000')
        self.assertFieldContains(page, 'donated', '2000')

    def assertAdopted(self, activity):
        self.assertEqual(activity.target.amount, 5000)
        self.assertEqual(str(activity.target.currency), 'EUR')


class GrantApplicationAdminTestCase(EventChildAdminTestMixin, BluebottleAdminTestCase):
    factory = GrantApplicationFactory
    adopted_model = GrantApplication
    linked_model = LinkedGrantApplication
    expected_fields = (
        'name', 'display_description', 'display_image', 'source', 'activity', 'url',
        'video_url', 'iri', 'start_time', 'end_time', 'target', 'location',
    )

    def assertExtraFields(self, page):
        self.assertFieldContains(page, 'target', '2500')

    def assertAdopted(self, activity):
        self.assertEqual(activity.target.amount, 2500)


class CollectCampaignAdminTestCase(EventChildAdminTestMixin, BluebottleAdminTestCase):
    factory = CollectCampaignFactory
    factory_kwargs = {
        'collect_type': 'Clothes',
        'target': 100,
        'donated': 25,
    }
    adopted_model = CollectActivity
    linked_model = LinkedCollectCampaign
    expected_fields = (
        'name', 'display_description', 'display_image', 'source', 'activity', 'url',
        'video_url', 'iri', 'start_time', 'end_time', 'location', 'collect_type',
        'target', 'donated', 'contributor_count',
    )

    def assertExtraFields(self, page):
        self.assertFieldContains(page, 'collect_type', 'Clothes')
        self.assertFieldContains(page, 'target', '100')
        self.assertFieldContains(page, 'donated', '25')

    def assertAdopted(self, activity):
        self.assertEqual(activity.collect_type.name, 'Clothes')
        self.assertEqual(activity.target, 100)


class DoGoodEventAdminTestCase(EventChildAdminTestMixin, BluebottleAdminTestCase):
    factory = DoGoodEventFactory
    factory_kwargs = {
        'slot_mode': None,
        'join_mode': None,
        'event_attendance_mode': 'OnlineEventAttendanceMode',
        'capacity': 10,
    }
    adopted_model = DeadlineActivity
    linked_model = LinkedDeadlineActivity
    expected_fields = (
        'name', 'display_description', 'display_image', 'source', 'activity', 'url',
        'video_url', 'iri', 'start_time', 'end_time', 'duration', 'application_deadline',
        'event_attendance_mode', 'repetition_mode', 'join_mode', 'slot_mode',
        'capacity', 'contributor_count',
    )

    def assertExtraFields(self, page):
        self.assertFieldContains(page, 'event_attendance_mode', 'online')
        self.assertFieldContains(page, 'capacity', '10')
        self.assertIsNone(page.html.find(id='sub_event-group'))


class DoGoodEventWithSubEventsAdminTestCase(DoGoodEventAdminTestCase):
    adopted_model = DateActivity
    linked_model = LinkedDateActivity

    def setUp(self):
        super().setUp()
        self.sub_events = SubEventFactory.create_batch(
            2,
            parent=self.event,
            event_attendance_mode='OnlineEventAttendanceMode',
            capacity=5,
        )

    def assertExtraFields(self, page):
        self.assertFieldContains(page, 'event_attendance_mode', 'online')
        inline = page.html.find(id='sub_event-group')
        self.assertIsNotNone(inline)
        self.assertIn('Slots', inline.text)
        for sub_event in self.sub_events:
            self.assertIn(sub_event.location.name, inline.text)

    def assertAdopted(self, activity):
        self.assertEqual(activity.slots.count(), 2)
