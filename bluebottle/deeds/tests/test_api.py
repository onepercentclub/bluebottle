import csv
from datetime import timedelta, date
import io

from rest_framework import status

from bluebottle.initiatives.models import InitiativePlatformSettings

from bluebottle.test.utils import APITestCase
from bluebottle.deeds.serializers import (
    DeedListSerializer, DeedSerializer, DeedTransitionSerializer,
    DeedParticipantSerializer, DeedParticipantTransitionSerializer
)
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from django.urls import reverse


class DeedsListViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.url = reverse('deed-list')
        self.serializer = DeedListSerializer
        self.factory = DeedFactory

        self.defaults = {
            'initiative': InitiativeFactory.create(status='approved', owner=self.user),
            'start': date.today() + timedelta(days=10),
            'end': date.today() + timedelta(days=20),
        }

        self.fields = ['initiative', 'start', 'end', 'title', 'description']

        settings = InitiativePlatformSettings.objects.get()
        settings.activity_types.append('deed')
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
        settings.activity_types.remove('deed')
        settings.save()

        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_403_FORBIDDEN)


class DeedsDetailViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.serializer = DeedSerializer
        self.factory = DeedFactory

        self.defaults = {
            'initiative': InitiativeFactory.create(status='approved'),
            'start': date.today() + timedelta(days=10),
            'end': date.today() + timedelta(days=20),
        }
        self.model = self.factory.create(**self.defaults)

        self.accepted_participants = DeedParticipantFactory.create_batch(
            5, activity=self.model, status='accepted'
        )
        self.withdrawn_participants = DeedParticipantFactory.create_batch(
            5, activity=self.model, status='withdrawn'
        )

        self.url = reverse('deed-detail', args=(self.model.pk, ))

        self.fields = ['initiative', 'start', 'end', 'title', 'description']

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
            self.accepted_participants + self.withdrawn_participants
        )

    def test_get_with_participant(self):
        participant = DeedParticipantFactory.create(activity=self.model, user=self.user)
        self.perform_get(user=self.user)

        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('initiative')
        self.assertIncluded('owner')
        self.assertIncluded('my-contributor', participant)

        self.assertPermission('PUT', False)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', False)
        self.assertRelationship(
            'contributors',
            self.accepted_participants + [participant]
        )

    def test_get_anonymous(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('initiative')
        self.assertIncluded('owner')

        self.assertPermission('PUT', False)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', False)

        self.assertRelationship('contributors', self.accepted_participants)

    def test_get_closed_site(self):
        with self.closed_site():
            self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_put(self):
        new_description = 'Test description'
        self.perform_update({'description': new_description}, user=self.model.owner)

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


class DeedTranistionListViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.url = reverse('deed-transition-list')
        self.serializer = DeedTransitionSerializer

        self.activity = DeedFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            start=date.today() + timedelta(days=10),
            end=date.today() + timedelta(days=20),
        )

        self.defaults = {
            'resource': self.activity,
            'transition': 'submit',
        }

        self.fields = ['resource', 'transition', ]

    def test_create(self):
        self.perform_create(user=self.activity.owner)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertIncluded('resource', self.activity)

        self.activity.refresh_from_db()
        self.assertEqual(self.defaults['resource'].status, 'open')

    def test_create_other_user(self):
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.activity.refresh_from_db()
        self.assertEqual(self.defaults['resource'].status, 'draft')

    def test_create_no_user(self):
        self.perform_create()
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.activity.refresh_from_db()
        self.assertEqual(self.defaults['resource'].status, 'draft')


class RelatedDeedParticipantViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.serializer = DeedParticipantSerializer
        self.factory = DeedParticipantFactory

        self.activity = DeedFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            start=date.today() + timedelta(days=10),
            end=date.today() + timedelta(days=20),
        )

        DeedParticipantFactory.create_batch(5, activity=self.activity, status='accepted')
        DeedParticipantFactory.create_batch(5, activity=self.activity, status='withdrawn')

        self.url = reverse('related-deed-participants', args=(self.activity.pk, ))

    def test_get(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(10)

        self.assertTrue(
            all(
                participant['attributes']['status'] in ('accepted', 'withdrawn')
                for participant in self.response.json()['data']
            )
        )

    def test_get_user(self):
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(5)

        self.assertTrue(
            all(
                participant['attributes']['status'] == 'accepted'
                for participant in self.response.json()['data']
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
                participant['attributes']['status'] == 'succeeded'
                for participant in self.response.json()['data']
            )
        )

    def test_get_anonymous(self):
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(5)

        self.assertTrue(
            all(
                participant['attributes']['status'] == 'accepted'
                for participant in self.response.json()['data']
            )
        )

    def test_get_closed_site(self):
        with self.closed_site():
            self.perform_get()
            self.assertStatus(status.HTTP_401_UNAUTHORIZED)


class DeedParticipantListViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.url = reverse('deed-participant-list')
        self.serializer = DeedParticipantSerializer
        self.factory = DeedParticipantFactory

        self.activity = DeedFactory.create(
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


class DeedParticipantTranistionListViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.url = reverse('deed-participant-transition-list')
        self.serializer = DeedParticipantTransitionSerializer

        self.participant = DeedParticipantFactory.create(
            activity=DeedFactory.create(
                initiative=InitiativeFactory.create(status='approved'),
                start=date.today() + timedelta(days=10),
                end=date.today() + timedelta(days=20),
            )
        )

        self.defaults = {
            'resource': self.participant,
            'transition': 'withdraw',
        }

        self.fields = ['resource', 'transition', ]

    def test_create(self):
        self.perform_create(user=self.participant.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertIncluded('resource', self.participant)

        self.participant.refresh_from_db()
        self.assertEqual(self.participant.status, 'withdrawn')

    def test_create_other_user(self):
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.participant.refresh_from_db()
        self.assertEqual(self.participant.status, 'accepted')

    def test_create_no_user(self):
        self.perform_create()
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.participant.refresh_from_db()
        self.assertEqual(self.participant.status, 'accepted')


class ParticipantExportViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_participant_exports = True
        initiative_settings.save()

        self.activity = DeedFactory.create(
            start=date.today() + timedelta(days=10),
            end=date.today() + timedelta(days=20),
        )

        self.participants = DeedParticipantFactory.create_batch(
            5, activity=self.activity
        )
        self.url = reverse('deed-detail', args=(self.activity.pk, ))

    @property
    def export_url(self):
        if self.response and self.response.json()['data']['attributes']['participants-export-url']:
            return self.response.json()['data']['attributes']['participants-export-url']['url']

    def test_get_owner(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        response = self.client.get(self.export_url)
        reader = csv.DictReader(io.StringIO(response.content.decode()))

        for row in reader:
            self.assertTrue('Email' in row)
            self.assertTrue('Name' in row)
            self.assertTrue('Registration Date' in row)
            self.assertTrue('Status' in row)

    def test_get_owner_incorrect_hash(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        response = self.client.get(self.export_url + 'test')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_participant(self):
        self.perform_get(user=self.participants[0].user)
        self.assertIsNone(self.export_url)

    def test_get_other_user(self):
        self.perform_get(user=self.user)
        self.assertIsNone(self.export_url)

    def test_get_no_user(self):
        self.perform_get()
        self.assertIsNone(self.export_url)
