from django.contrib.auth.models import Permission
from django.test.utils import override_settings
from django.urls import reverse
from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.models import Activity
from bluebottle.test.elasticsearch import (
    ElasticsearchTestCase, SearchJSONAPITestClient, refresh_search_indices
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.time_based.models import Registration
from bluebottle.time_based.tests.factories import (
    DeadlineActivityFactory, DeadlineRegistrationFactory, InterestFactory
)


class ActionApiTestCase(ElasticsearchTestCase):
    def setUp(self):
        super().setUp()
        self.client = SearchJSONAPITestClient()
        self.url = reverse('cta-action-list')
        self.owner = BlueBottleUserFactory.create()
        self.other = BlueBottleUserFactory.create()

    def index(self, activity):
        registry.update(Activity.objects.get(pk=activity.pk))
        refresh_search_indices()

    def actions(self, user):
        response = self.client.get(self.url, user=user)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_accepts_json_api(self):
        response = self.client.get(self.url, user=self.owner, HTTP_ACCEPT='application/vnd.api+json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')

    def test_no_actions(self):
        data = self.actions(self.owner)
        self.assertEqual(data['data'], [])
        self.assertEqual(data['meta']['count'], 0)

    def pending_registrations_activity(self):
        activity = DeadlineActivityFactory.create(status='open', review=True, owner=self.owner)
        DeadlineRegistrationFactory.create(activity=activity)
        self.index(activity)
        return activity

    def test_pending_registrations(self):
        activity = self.pending_registrations_activity()

        data = self.actions(self.owner)
        self.assertEqual(data['meta']['count'], 1)
        action = data['data'][0]
        self.assertEqual(action['id'], 'pending_registrations-{}'.format(activity.pk))
        self.assertEqual(action['attributes']['actionType'], 'pending_registrations')
        self.assertEqual(action['attributes']['count'], 1)
        self.assertEqual(action['attributes']['severity'], 'urgent')
        self.assertTrue(action['attributes']['url'].startswith('/activities/details/deadline/'))

    def test_pending_registrations_other_user(self):
        self.pending_registrations_activity()
        self.assertEqual(self.actions(self.other)['data'], [])

    def test_pending_registrations_resolved(self):
        activity = self.pending_registrations_activity()
        Registration.objects.filter(activity=activity).update(status='accepted')
        self.index(activity)

        self.assertEqual(self.actions(self.owner)['data'], [])

    def test_waiting_list(self):
        activity = DeadlineActivityFactory.create(status='full', owner=self.owner)
        InterestFactory.create(activity=activity)
        self.index(activity)

        types = [a['attributes']['actionType'] for a in self.actions(self.owner)['data']]
        self.assertEqual(types, ['waiting_list'])

    def test_needs_work(self):
        activity = DeadlineActivityFactory.create(status='needs_work', owner=self.owner)
        self.index(activity)

        types = [a['attributes']['actionType'] for a in self.actions(self.owner)['data']]
        self.assertEqual(types, ['needs_work'])

    def test_dismiss(self):
        activity = self.pending_registrations_activity()
        action_id = 'pending_registrations-{}'.format(activity.pk)

        response = self.client.delete(reverse('cta-action-detail', args=(action_id,)), user=self.owner)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.actions(self.owner)['data'], [])
        self.assertEqual(len(self.actions(self.owner)['data']), 0)

    def test_dismiss_unknown_type(self):
        response = self.client.delete(reverse('cta-action-detail', args=('foo-1',)), user=self.owner)
        self.assertEqual(response.status_code, 404)

    def test_snooze(self):
        activity = self.pending_registrations_activity()
        url = reverse('cta-action-detail', args=('pending_registrations-{}'.format(activity.pk),))

        response = self.client.patch(
            url, {'data': {'attributes': {'snoozeDays': 3}}}, user=self.owner
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.actions(self.owner)['data'], [])

    def test_snooze_kebab_case_attributes(self):
        activity = self.pending_registrations_activity()
        url = reverse('cta-action-detail', args=('pending_registrations-{}'.format(activity.pk),))

        response = self.client.patch(url, {'data': {'attributes': {'snooze-days': 3}}}, user=self.owner)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['attributes']['actionType'], 'pending_registrations')
        self.assertIsNotNone(response.json()['data']['attributes']['snoozedUntil'])

    def test_snoozed_not_counted(self):
        activity = self.pending_registrations_activity()
        url = reverse('cta-action-detail', args=('pending_registrations-{}'.format(activity.pk),))
        self.client.patch(url, {'data': {'attributes': {'snoozeDays': 3}}}, user=self.owner)

        data = self.actions(self.owner)
        self.assertEqual(data['meta']['count'], 0)
        self.assertEqual(data['data'], [])

        response = self.client.get(self.url + '?filter[snoozed]=1', user=self.owner)
        data = response.json()
        self.assertEqual(data['meta']['count'], 0)
        self.assertEqual(len(data['data']), 1)
        self.assertIsNotNone(data['data'][0]['attributes']['snoozedUntil'])

    def test_ignored_not_listed_with_snoozed(self):
        activity = self.pending_registrations_activity()
        url = reverse('cta-action-detail', args=('pending_registrations-{}'.format(activity.pk),))
        self.client.delete(url, user=self.owner)

        response = self.client.get(self.url + '?filter[snoozed]=1', user=self.owner)
        self.assertEqual(response.json()['data'], [])

    def test_pagination_meta(self):
        meta = self.actions(self.owner)['meta']
        self.assertEqual(meta['pagination'], {'page': 1, 'pages': 1, 'count': 0})

    def test_snooze_expired(self):
        activity = self.pending_registrations_activity()
        url = reverse('cta-action-detail', args=('pending_registrations-{}'.format(activity.pk),))
        self.client.patch(url, {'data': {'attributes': {'snoozeDays': 3}}}, user=self.owner)
        self.owner.action_dismissals.update(snoozed_until='2000-01-01T00:00:00Z')

        self.assertEqual(len(self.actions(self.owner)['data']), 1)

    def test_dismiss_is_per_user(self):
        activity = DeadlineActivityFactory.create(status='open', review=True, owner=self.owner)
        activity.initiative.owner = self.other
        activity.initiative.save()
        DeadlineRegistrationFactory.create(activity=activity)
        self.index(activity)

        url = reverse('cta-action-detail', args=('pending_registrations-{}'.format(activity.pk),))
        self.client.delete(url, user=self.owner)

        self.assertEqual(len(self.actions(self.other)['data']), 1)

    def test_platform_manager_review(self):
        reviewer = BlueBottleUserFactory.create()
        reviewer.user_permissions.add(Permission.objects.get(codename='api_review_activity'))
        activity = DeadlineActivityFactory.create(status='submitted')
        self.index(activity)

        action = self.actions(reviewer)['data'][0]
        self.assertEqual(action['attributes']['actionType'], 'review_submitted')
        self.assertEqual(action['attributes']['count'], 1)

    @override_settings(CTA_DEMO_ACTIONS=True)
    def test_demo_actions(self):
        self.pending_registrations_activity()
        demo = [a for a in self.actions(self.owner)['data'] if a['attributes']['isDemo']]
        self.assertEqual({a['attributes']['actionType'] for a in demo}, {'thank_participants', 'low_engagement'})

    def test_permission_flag(self):
        self.pending_registrations_activity()
        response = self.client.get(reverse('user-current'), user=self.owner)
        self.assertTrue(response.json()['permissions']['my_actions'])
        response = self.client.get(reverse('user-current'), user=self.other)
        self.assertFalse(response.json()['permissions']['my_actions'])
