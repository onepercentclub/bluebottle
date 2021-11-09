import csv
from datetime import timedelta, date
import io

from rest_framework import status

from bluebottle.collect.serializers import CollectActivityListSerializer, CollectActivitySerializer, \
    CollectActivityTransitionSerializer, CollectContributorSerializer, CollectContributorTransitionSerializer
from bluebottle.collect.tests.factories import CollectActivityFactory, CollectContributorFactory, CollectTypeFactory
from bluebottle.initiatives.models import InitiativePlatformSettings

from bluebottle.test.utils import APITestCase
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from django.urls import reverse


class CollectActivityListViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.url = reverse('collect-activity-list')
        self.serializer = CollectActivityListSerializer
        self.factory = CollectActivityFactory
        self.collect_type = CollectTypeFactory.create()

        self.defaults = {
            'initiative': InitiativeFactory.create(status='approved', owner=self.user),
            'start': date.today() + timedelta(days=10),
            'end': date.today() + timedelta(days=20),
            'collect_type': self.collect_type
        }

        self.fields = ['initiative', 'start', 'end', 'title', 'description', 'collect_type']

        settings = InitiativePlatformSettings.objects.get()
        settings.activity_types.append('collect')
        settings.save()

    def test_create_complete(self):
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertIncluded('initiative')
        self.assertIncluded('owner')

        self.assertAttribute('start')
        self.assertAttribute('end')

        self.assertPermission('PUT', True)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', True)
        self.assertTransition('submit')
        self.assertTransition('delete')

    def test_create_incomplete(self):
        self.defaults['description'] = ''
        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_201_CREATED)
        self.assertRequired('description')

    def test_create_error(self):
        self.defaults['start'] = self.defaults['end'] + timedelta(days=2)
        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_201_CREATED)
        self.assertHasError('end', 'The end date should be after the start date')

    def test_create_other_user(self):
        self.perform_create(user=BlueBottleUserFactory.create())
        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_create_other_user_is_open(self):
        self.defaults['initiative'].is_open = True
        self.defaults['initiative'].save()

        self.perform_create(user=BlueBottleUserFactory.create())
        self.assertStatus(status.HTTP_201_CREATED)

    def test_create_other_user_is_open_not_approved(self):
        self.defaults['initiative'].is_open = True
        self.defaults['initiative'].states.cancel(save=True)

        self.perform_create(user=BlueBottleUserFactory.create())
        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_create_anonymous(self):
        self.perform_create()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_create_disabled_activity_type(self):
        settings = InitiativePlatformSettings.objects.get()
        settings.activity_types.remove('collect')
        settings.save()

        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_403_FORBIDDEN)


class CollectActivitysDetailViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.serializer = CollectActivitySerializer
        self.factory = CollectActivityFactory
        self.collect_type = CollectTypeFactory.create()

        self.defaults = {
            'initiative': InitiativeFactory.create(status='approved'),
            'start': date.today() + timedelta(days=10),
            'end': date.today() + timedelta(days=20),
            'type': self.collect_type
        }
        self.model = self.factory.create(**self.defaults)

        self.active_contributors = CollectContributorFactory.create_batch(
            5, activity=self.model
        )
        self.withdrawn_contributors = CollectContributorFactory.create_batch(
            5, activity=self.model, status='withdrawn'
        )

        self.url = reverse('collect-activity-detail', args=(self.model.pk, ))

        self.fields = ['initiative', 'start', 'end', 'title', 'description', 'type']

    def test_get(self):
        self.perform_get(user=self.model.owner)

        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('initiative')
        self.assertIncluded('owner')

        self.assertAttribute('start')
        self.assertAttribute('end')

        self.assertPermission('PUT', True)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', True)

        self.assertTransition('submit')
        self.assertTransition('delete')
        self.assertRelationship(
            'contributors',
            self.active_contributors + self.withdrawn_contributors
        )

    def test_get_with_contributor(self):
        contributor = CollectContributorFactory.create(activity=self.model, user=self.user)
        self.perform_get(user=self.user)

        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('initiative')
        self.assertIncluded('owner')
        self.assertIncluded('my-contributor', contributor)

        self.assertPermission('PUT', False)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', False)
        self.assertRelationship(
            'contributors',
            self.active_contributors + [contributor]
        )
        links = self.response.data['links']

        self.assertTrue(f'/api/collect/ical/{self.model.id}' in links['ical'])
        start = self.model.start.strftime('%Y%m%d')
        end = self.model.end + timedelta(days=1)
        end = end.strftime('%Y%m%d')
        self.assertTrue(f'dates={start}%2F{end}' in links['google'])

    def test_get_anonymous(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('initiative')
        self.assertIncluded('owner')

        self.assertPermission('PUT', False)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', False)

        self.assertRelationship('contributors', self.active_contributors)

    def test_get_closed_site(self):
        with self.closed_site():
            self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_put(self):
        new_description = 'Test description'
        self.perform_update({'description': new_description}, user=self.model.owner)

        self.assertStatus(status.HTTP_200_OK)

        self.assertAttribute('description', new_description)

    def test_put_initiative_owner(self):
        new_description = 'Test description'
        self.perform_update({'description': new_description}, user=self.model.initiative.owner)

        self.assertStatus(status.HTTP_200_OK)

        self.assertAttribute('description', new_description)

    def test_put_initiative_activity_manager(self):
        new_description = 'Test description'
        self.perform_update(
            {'description': new_description},
            user=self.model.initiative.activity_managers.first()
        )

        self.assertStatus(status.HTTP_200_OK)

        self.assertAttribute('description', new_description)

    def test_other_user(self):
        new_description = 'Test description'
        self.perform_update({'description': new_description}, user=self.user)

        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_no_user(self):
        new_description = 'Test description'
        self.perform_update({'description': new_description})

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)


class CollectActivityTransitionListViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.url = reverse('collect-activity-transition-list')
        self.serializer = CollectActivityTransitionSerializer

        self.activity = CollectActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            start=date.today() + timedelta(days=10),
            end=date.today() + timedelta(days=20),
        )

        self.defaults = {
            'resource': self.activity,
            'transition': 'submit',
        }

        self.fields = ['resource', 'transition', ]

    def test_submit(self):
        self.perform_create(user=self.activity.owner)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertIncluded('resource', self.activity)

        self.activity.refresh_from_db()
        self.assertEqual(self.defaults['resource'].status, 'open')

    def test_submit_other_user(self):
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.activity.refresh_from_db()
        self.assertEqual(self.defaults['resource'].status, 'draft')

    def test_submit_no_user(self):
        self.perform_create()
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.activity.refresh_from_db()
        self.assertEqual(self.defaults['resource'].status, 'draft')


class RelatedCollectActivityContributorViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.serializer = CollectContributorSerializer
        self.factory = CollectContributorFactory

        self.activity = CollectActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            start=date.today() + timedelta(days=10),
            end=date.today() + timedelta(days=20),
        )

        CollectContributorFactory.create_batch(5, activity=self.activity)
        CollectContributorFactory.create_batch(5, activity=self.activity, status='withdrawn')

        self.url = reverse('related-collect-contributors', args=(self.activity.pk, ))

    def test_get(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(10)

        self.assertTrue(
            all(
                contributor['attributes']['status'] in ('succeeded', 'withdrawn')
                for contributor in self.response.json()['data']
            )
        )

    def test_get_user(self):
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(5)

        self.assertTrue(
            all(
                contributor['attributes']['status'] == 'succeeded'
                for contributor in self.response.json()['data']
            )
        )

    def test_get_user_succeeded(self):
        self.activity.start = date.today() - timedelta(days=10)
        self.activity.end = date.today() - timedelta(days=5)
        self.activity.save()

        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(5)

        self.assertTrue(
            all(
                contributor['attributes']['status'] == 'succeeded'
                for contributor in self.response.json()['data']
            )
        )

    def test_get_anonymous(self):
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(5)

        self.assertTrue(
            all(
                contributor['attributes']['status'] == 'succeeded'
                for contributor in self.response.json()['data']
            )
        )

    def test_get_closed_site(self):
        with self.closed_site():
            self.perform_get()
            self.assertStatus(status.HTTP_401_UNAUTHORIZED)


class CollectActivityContributorListViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.url = reverse('collect-contributor-list')
        self.serializer = CollectContributorSerializer
        self.factory = CollectContributorFactory

        self.activity = CollectActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            start=date.today() + timedelta(days=10),
            end=date.today() + timedelta(days=20),
        )

        self.defaults = {
            'activity': self.activity
        }

        self.fields = ['activity']

    def test_create(self):
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertIncluded('activity')
        self.assertIncluded('user')

        self.assertPermission('PUT', True)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', True)

        self.assertTransition('withdraw')

    def test_create_anonymous(self):
        self.perform_create()
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)


class CollectActivityContributorTranistionListViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.url = reverse('collect-contributor-transition-list')
        self.serializer = CollectContributorTransitionSerializer

        self.contributor = CollectContributorFactory.create(
            activity=CollectActivityFactory.create(
                initiative=InitiativeFactory.create(status='approved'),
                start=date.today() + timedelta(days=10),
                end=date.today() + timedelta(days=20),
            )
        )

        self.defaults = {
            'resource': self.contributor,
            'transition': 'withdraw',
        }

        self.fields = ['resource', 'transition', ]

    def test_create(self):
        self.perform_create(user=self.contributor.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertIncluded('resource', self.contributor)

        self.contributor.refresh_from_db()
        self.assertEqual(self.contributor.status, 'withdrawn')

    def test_create_other_user(self):
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.contributor.refresh_from_db()
        self.assertEqual(self.contributor.status, 'succeeded')

    def test_create_no_user(self):
        self.perform_create()
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.contributor.refresh_from_db()
        self.assertEqual(self.contributor.status, 'succeeded')


class ContributorExportViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_participant_exports = True
        initiative_settings.save()

        self.activity = CollectActivityFactory.create(
            start=date.today() + timedelta(days=10),
            end=date.today() + timedelta(days=20),
        )

        self.contributors = CollectContributorFactory.create_batch(
            5, activity=self.activity
        )
        self.url = reverse('collect-activity-detail', args=(self.activity.pk, ))

    @property
    def export_url(self):
        if self.response and self.response.json()['data']['attributes']['contributors-export-url']:
            return self.response.json()['data']['attributes']['contributors-export-url']['url']

    def test_get_owner(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTrue(self.export_url)
        response = self.client.get(self.export_url)
        reader = csv.DictReader(io.StringIO(response.content.decode()))
        self.assertEqual(reader.fieldnames, ['Email', 'Name', 'Registration Date', 'Status'])

    def test_get_owner_incorrect_hash(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        response = self.client.get(self.export_url + 'test')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_contributor(self):
        self.perform_get(user=self.contributors[0].user)
        self.assertIsNone(self.export_url)

    def test_get_other_user(self):
        self.perform_get(user=self.user)
        self.assertIsNone(self.export_url)

    def test_get_no_user(self):
        self.perform_get()
        self.assertIsNone(self.export_url)
