from io import BytesIO

import mock
import requests
from django.contrib.admin.sites import AdminSite
from django.core.files import File
from django.urls import reverse

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.admin import FollowerAdmin, FollowingAdminForm, PublishedActivityAdmin
from bluebottle.activity_pub.effects import get_platform_actor
from bluebottle.activity_pub.models import Accept, Follow, Follower, Following, PublishedActivity, Recipient
from bluebottle.activity_pub.tests.factories import OrganizationFactory
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.utils import BluebottleAdminTestCase
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
