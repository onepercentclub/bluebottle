import io
from datetime import timedelta, date

from django.urls import reverse
from openpyxl import load_workbook
from rest_framework import status

from bluebottle.files.models import RelatedImage
from bluebottle.deeds.serializers import (
    DeedListSerializer, DeedSerializer, DeedTransitionSerializer,
    DeedParticipantSerializer, DeedParticipantTransitionSerializer
)
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.files.tests.factories import ImageFactory
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.tests.factories import SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import APITestCase


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

    def test_create_description_images(self):
        image1 = ImageFactory.create()
        image2 = ImageFactory.create()

        self.defaults['description'] = f"""
            <img src="{reverse('upload-image-preview', args=(image1.pk, '292x164'))}"> Text with an image
            <img src="{reverse('upload-image-preview', args=(image2.pk, '292x164'))}"> and another one
        """
        
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)

        self.assertEqual(RelatedImage.objects.count(), 2)

        for image in RelatedImage.objects.all():
            self.assertTrue(
                reverse('related-activity-image-content', args=(image.pk, '600')) 
                in self.response.json()['data']['attributes']['description']
            )

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
            'description': 'Some descrpition',
            'start': date.today() + timedelta(days=10),
            'end': date.today() + timedelta(days=20),
        }
        self.model = self.factory.create(**self.defaults)

        self.accepted_participants = DeedParticipantFactory.create_batch(
            4, activity=self.model, status='accepted'
        )
        self.withdrawn_participants = DeedParticipantFactory.create_batch(
            4, activity=self.model, status='withdrawn'
        )

        self.url = reverse('deed-detail', args=(self.model.pk,))

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
        self.assertMeta(
            'contributor-count',
            len(self.accepted_participants)
        )
        contributors = self.loadLinkedRelated('contributors')
        self.assertObjectList(
            contributors,
            (self.accepted_participants + self.withdrawn_participants).reverse()
        )
        self.assertTrue(
            self.response.json()['data']['relationships']['updates']['links']['related'].endswith(
                reverse('activity-update-list', args=(self.model.pk,))
            ),
        )

    def test_get_with_segments(self):
        segment = SegmentFactory.create(
            name="SDG1"
        )
        self.model.segments.add(segment)
        self.model.save()
        self.perform_get(user=self.model.owner)

        self.assertStatus(status.HTTP_200_OK)

        self.assertRelationship('segments', [segment])

    def test_get_closed_segment(self):
        segment = SegmentFactory.create(
            name="SDG1",
            closed=True
        )
        self.model.segments.add(segment)
        self.model.save()
        self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_get_closed_segment_logged_in(self):
        segment = SegmentFactory.create(
            name="SDG1",
            closed=True
        )
        self.model.segments.add(segment)
        self.model.save()
        self.perform_get(user=BlueBottleUserFactory.create())

        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_get_closed_segment_logged_in_with_segment(self):
        segment = SegmentFactory.create(
            name="SDG1",
            closed=True
        )

        SegmentFactory.create(
            name="SDG2",
            closed=True
        )

        self.model.segments.add(segment)
        self.model.save()
        user = BlueBottleUserFactory.create()
        user.segments.add(segment)
        user.save()
        self.perform_get(user=user)

        self.assertStatus(status.HTTP_200_OK)

    def test_get_calendar_links(self):
        self.perform_get(user=self.model.owner)

        links = self.response.json()['data']['attributes']['links']

        self.assertTrue(
            links['ical'].startswith(
                reverse('deed-ical', args=(self.model.pk,))
            )
        )

    def test_get_with_participant(self):
        participant = DeedParticipantFactory.create(
            activity=self.model,
            status='withdrawn',
            user=self.user
        )
        self.perform_get(user=self.user)

        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('initiative')
        self.assertIncluded('owner')
        self.assertIncluded('my-contributor', participant)

        self.assertPermission('PUT', False)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', False)
        self.assertMeta(
            'contributor-count',
            len(self.accepted_participants)
        )
        contributors = self.loadLinkedRelated('contributors')
        self.assertObjectList(
            contributors,
            (self.accepted_participants + [participant]).reverse()
        )

    def test_get_with_participant_team(self):
        self.model.team_activity = 'teams'
        self.model.save()

        participant = DeedParticipantFactory.create(
            activity=self.model,
            user=self.user
        )
        self.perform_get(user=self.user)

        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('my-contributor', participant)
        self.assertIncluded('my-contributor.invite', participant.invite)

    def test_get_anonymous(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('initiative')
        self.assertIncluded('owner')

        self.assertPermission('PUT', False)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', False)
        self.assertMeta(
            'contributor-count',
            len(self.accepted_participants)
        )
        contributors = self.loadLinkedRelated('contributors')
        self.assertObjectList(
            contributors,
            self.accepted_participants.reverse()
        )

    def test_get_closed_site(self):
        with self.closed_site():
            self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_put(self):
        new_description = 'Test description'
        self.perform_update({'description': new_description}, user=self.model.owner)

        self.assertStatus(status.HTTP_200_OK)

        self.assertAttribute('description', new_description)

    def test_put_start_after_end(self):
        self.model.status = 'open'
        self.model.save()

        self.perform_update(
            {'start': date.today() + timedelta(days=10), 'end': date.today() + timedelta(days=5)},
            user=self.model.owner
        )

        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_put_missing_description(self):
        self.perform_update(
            {
                'title': '',
                'description': '',
                'start': None,
                'end': None,
            },
            user=self.model.owner
        )
        self.assertStatus(status.HTTP_200_OK)

        self.model.refresh_from_db()
        self.assertAttribute('description', '')
        self.assertAttribute('title', '')
        self.assertAttribute('start', None)
        self.assertAttribute('end', None)

    def test_put_open_missing_description(self):
        self.model.status = 'open'
        self.model.save()

        self.perform_update(
            {
                'title': '',
                'description': '',
                'start': None,
                'end': None,
            },
            user=self.model.owner
        )

        self.assertStatus(status.HTTP_400_BAD_REQUEST)
        self.assertError('title')
        self.assertError('description')

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


class DeedTransitionListViewAPITestCase(APITestCase):
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

        self.url = reverse('related-deed-participants', args=(self.activity.pk,))

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

        for member in self.get_included('user'):
            self.assertIsNotNone(member['attributes']['last-name'])

    def test_get_staff(self):
        self.perform_get(user=BlueBottleUserFactory.create(is_staff=True))
        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(10)

        self.assertTrue(
            all(
                participant['attributes']['status'] in ('accepted', 'withdrawn')
                for participant in self.response.json()['data']
            )
        )

        for member in self.get_included('user'):
            self.assertIsNotNone(member['attributes']['last-name'])

    def test_get_hide_first_name(self):
        MemberPlatformSettings.objects.update_or_create(display_member_names='first_name')

        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        for member in self.get_included('user'):
            self.assertIsNotNone(member['attributes']['last-name'])

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

    def test_get_user_hide_first_name(self):
        DeedParticipantFactory.create(
            activity=self.activity, status='accepted', user=self.activity.owner
        )
        MemberPlatformSettings.objects.update_or_create(display_member_names='first_name')

        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)

        for member in self.get_included('user'):
            if member['id'] == str(self.activity.owner.pk):
                self.assertIsNotNone(member['attributes']['last-name'])
                self.assertEqual(member['attributes']['full-name'], self.activity.owner.full_name)
            else:
                self.assertIsNone(member['attributes']['last-name'])
                self.assertEqual(member['attributes']['full-name'], member['attributes']['first-name'])

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

    def test_get_anonymous_hide_first_name(self):
        MemberPlatformSettings.objects.update_or_create(display_member_names='first_name')

        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)

        for member in self.get_included('user'):
            self.assertIsNone(member['attributes']['last-name'])

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

        self.fields = ['activity', 'accepted_invite']

    def test_create(self):
        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_201_CREATED)

        self.assertIncluded('activity')
        self.assertIncluded('user')

        self.assertPermission('PUT', True)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', True)

        self.assertTransition('withdraw')
        self.assertIncluded('invite')

    def test_create_required_question(self):
        MemberPlatformSettings.objects.update_or_create(
            required_questions_location='contribution', require_birthdate=True
        )
        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.response.json()['errors'][0]['code'], 'required')

    def test_create_with_team_invite(self):
        self.activity.team_activity = 'teams'
        self.activity.save()

        team_captain = DeedParticipantFactory.create(activity=self.activity)

        self.defaults['accepted_invite'] = team_captain.invite

        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_201_CREATED)
        self.assertRelationship('team', [team_captain.team])

    def test_create_anonymous(self):
        self.perform_create()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)


class DeedParticipantTransitionListViewAPITestCase(APITestCase):
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
        self.url = reverse('deed-detail', args=(self.activity.pk,))

    @property
    def export_url(self):
        if self.response and self.response.json()['data']['attributes']['participants-export-url']:
            return self.response.json()['data']['attributes']['participants-export-url']['url']

    def test_get_owner(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        response = self.client.get(self.export_url)

        sheet = load_workbook(filename=io.BytesIO(response.content)).get_active_sheet()
        rows = list(sheet.values)
        self.assertEqual(
            rows[0], ('Email', 'Name', 'Registration Date', 'Status')
        )

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


class DeedParticipantDetailViewAPITestCase(APITestCase):
    serializer = DeedParticipantSerializer

    def setUp(self):
        super().setUp()

        self.activity = DeedFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            start=date.today() + timedelta(days=10),
            end=date.today() + timedelta(days=20),
        )
        self.participant = DeedParticipantFactory.create(activity=self.activity)
        self.url = reverse('deed-participant-detail', args=(self.participant.pk,))

    def test_get_user(self):
        self.perform_get(user=self.participant.user)

        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('activity', self.activity)
        self.assertIncluded('user', self.participant.user)
        self.assertRelationship('invite', [self.participant.invite])
        self.assertRelationship('accepted-invite')

    def test_get_other_user(self):
        self.perform_get(user=BlueBottleUserFactory.create())

        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('activity', self.activity)
        self.assertIncluded('user', self.participant.user)
        self.assertNoRelationship('invite')
        self.assertRelationship('accepted-invite')

    def test_get_accepted_invite(self):
        invite = DeedParticipantFactory.create().invite
        self.participant.accepted_invite = invite
        self.participant.save()

        self.perform_get(user=self.participant.user)

        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('activity', self.activity)
        self.assertIncluded('user', self.participant.user)
        self.assertNoRelationship('invite')
        self.assertRelationship('accepted-invite')

    def test_get_anonymous(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('activity', self.activity)
        self.assertIncluded('user', self.participant.user)
        self.assertNoRelationship('invite')
        self.assertRelationship('accepted-invite')

    def test_get_anonymous_closed_site(self):
        with self.closed_site():
            self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)
