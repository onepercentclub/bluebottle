from datetime import date, timedelta
from io import BytesIO

from rest_framework import status
from django.urls import reverse
from openpyxl import load_workbook

from bluebottle.initiatives.tests.factories import InitiativeFactory

from bluebottle.members.models import MemberPlatformSettings
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.segments.tests.factories import SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.files.tests.factories import PrivateDocumentFactory


class TimeBasedActivityListAPITestCase:
    fields = ['initiative', 'start', 'title', 'description', 'review']

    attributes = ['start', 'title', 'description', 'review']
    relationships = ['initiative', 'owner']
    included = ['initiative', 'owner']

    @property
    def model_name(self):
        return self.factory._meta.model._meta.model_name

    def setUp(self):
        self.url = reverse(self.url_name)

        settings = InitiativePlatformSettings.objects.get()
        settings.activity_types.append(self.model_name)
        settings.save()
        super().setUp()

    def test_create_complete(self):
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)

        for relationship in self.relationships:
            self.assertRelationship(relationship)

        for included in self.included:
            self.assertIncluded(included)

        for attribute in self.attributes:
            self.assertAttribute(attribute)

        self.assertPermission('PUT', True)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', True)

        self.assertTransition('publish')
        self.assertTransition('delete')

    def test_create_incomplete(self):
        self.defaults['description'] = ''
        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_201_CREATED)
        self.assertRequired('description')

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
        settings.activity_types.remove(self.model_name)
        settings.save()

        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_403_FORBIDDEN)


class TimeBasedActivityDetailAPITestCase:
    url_name = 'deed-detail'

    fields = ['initiative', 'start', 'title', 'description', 'review']

    attributes = ['start', 'title', 'description', 'review']
    relationships = ['initiative', 'owner']
    included = ['initiative', 'owner']

    defaults = {
        'title': 'Test title',
        'description': 'Test description',
        'review': False,
        'is_online': True,
    }

    def setUp(self):
        self.model = self.factory.create(
            initiative=InitiativeFactory.create(status='approved'),
            **self.defaults
        )

        self.url = reverse(self.url_name, args=(self.model.pk,))

        super().setUp()

    def test_get(self):
        self.perform_get(user=self.model.owner)

        self.assertStatus(status.HTTP_200_OK)

        for relationship in self.relationships:
            self.assertRelationship(relationship)

        for included in self.included:
            self.assertIncluded(included)

        for attribute in self.attributes:
            self.assertAttribute(attribute)

        self.assertPermission('PUT', True)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', True)

        self.assertTransition('publish')
        self.assertTransition('delete')

    def test_export_url_disabled(self):
        self.perform_get(user=self.model.owner)
        self.assertStatus(status.HTTP_200_OK)

        self.assertIsNone(
            self.response.json()['data']['attributes']['participants-export-url']
        )

    def test_export_url(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_participant_exports = True
        initiative_settings.save()

        self.perform_get(user=self.model.owner)
        self.assertStatus(status.HTTP_200_OK)

        self.assertTrue(
            'url' in self.response.json()['data']['attributes']['participants-export-url']
        )

    def test_export_url_other_user(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_participant_exports = True
        initiative_settings.save()

        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)

        self.assertIsNone(
            self.response.json()['data']['attributes']['participants-export-url']

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

    def test_get_anonymous(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('initiative')
        self.assertIncluded('owner')

        self.assertPermission('PUT', False)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', False)

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
            {'start': date.today() + timedelta(days=10), 'deadline': date.today() + timedelta(days=5)},
            user=self.model.owner
        )

        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_put_missing_description(self):
        self.perform_update(
            {
                'description': '',
            },
            user=self.model.owner
        )
        self.assertStatus(status.HTTP_200_OK)

        self.model.refresh_from_db()
        self.assertAttribute('description', '')
        self.assertRequired('description')

    def test_put_open_missing_description(self):
        self.model.status = 'open'
        self.model.save()

        self.perform_update(
            {
                'description': '',
            },
            user=self.model.owner
        )

        self.assertStatus(status.HTTP_400_BAD_REQUEST)
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


class TimeBasedActivityTransitionListAPITestCase:
    defaults = {
        'title': 'Test title',
        'description': 'Test description',
        'review': False,
        'is_online': True,
    }

    def setUp(self):
        self.activity = self.activity_factory.create(
            **self.defaults,
            initiative=InitiativeFactory.create(status='approved'),
        )
        self.url = reverse(self.url_name)

        self.defaults = {
            'resource': self.activity,
            'transition': 'publish',
        }
        super().setUp()

    def test_publish(self):
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


class TimeBasedRegistrationListAPITestCase:
    included = ['activity', 'user']
    fields = ['answer', 'document', 'activity']

    def setUp(self):
        super().setUp()

        self.url = reverse(self.url_name)

        self.activity = self.activity_factory.create(
            **self.activity_defaults,
            review_title='document',
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
        )

        self.defaults = {
            'activity': self.activity,
        }

    def test_create(self):
        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_201_CREATED)

        for included in self.included:
            self.assertIncluded(included)

        self.assertAttribute('answer')
        self.assertRelationship('document')

        self.assertPermission('PUT', True)
        self.assertPermission('GET', True)
        self.assertPermission('PATCH', True)

    def test_create_require_answer(self):
        self.activity.registration_flow = 'question'
        self.activity.save()

        self.defaults['answer'] = None
        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_require_document(self):
        self.activity.registration_flow = 'question'
        self.activity.review_document_enabled = True
        self.activity.save()

        self.defaults['answer'] = 'Some answer'
        self.defaults['document'] = None

        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_require_document_complete(self):
        self.activity.registration_flow = 'question'
        self.activity.review_document_enabled = True
        self.activity.save()

        self.defaults['answer'] = 'Some answer'
        self.defaults['document'] = PrivateDocumentFactory.create()

        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_201_CREATED)

    def test_create_required_profile_question(self):
        MemberPlatformSettings.objects.update_or_create(
            required_questions_location='contribution', require_birthdate=True
        )
        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.response.json()['errors'][0]['code'], 'required')

    def test_create_anonymous(self):
        self.perform_create()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)


class TimeBasedRegistrationRelatedAPIListTestCase:
    def setUp(self):
        self.activity = self.activity_factory.create(
            **self.activity_defaults,
            review_title='document',
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
        )
        self.factory.create_batch(5, activity=self.activity, status='accepted')
        self.factory.create_batch(5, activity=self.activity, status='rejected')

        self.url = reverse(self.url_name, args=(self.activity.pk,))

        super().setUp()

    def test_get(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(10)

        self.assertTrue(
            all(
                participant['meta']['current-status']['value'] in ('accepted', 'rejected')
                for participant in self.response.json()['data']
            )
        )

        for member in self.get_included('user'):
            self.assertIsNotNone(member['attributes']['last-name'])

    def test_get_filter_my_registration(self):
        registration = self.factory.create(activity=self.activity, status='accepted')
        self.perform_get(user=registration.user, query={'filter[my]': 1})
        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(1)

        self.assertObjectList(
            [registration]
        )

    def test_get_staff(self):
        self.perform_get(user=BlueBottleUserFactory.create(is_staff=True))
        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(10)

        self.assertTrue(
            all(
                participant['meta']['current-status']['value'] in ('accepted', 'rejected')
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
                participant['meta']['current-status']['value'] == 'accepted'
                for participant in self.response.json()['data']
            )
        )

    def test_get_user_hide_first_name(self):
        self.factory.create(
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

    def test_get_anonymous(self):
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(5)

        self.assertTrue(
            all(
                participant['meta']['current-status']['value'] == 'accepted'
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


class TimeBasedRegistrationDetailAPITestCase:
    included = ['user', 'activity']

    def setUp(self):
        self.activity = self.activity_factory.create(
            **self.activity_defaults,
            review_title='document',
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
        )
        self.defaults = {
            'answer': 'Some answer',
            'document': PrivateDocumentFactory.create(),
            'activity': self.activity
        }
        self.model = self.factory.create(**self.defaults)
        self.url = reverse(self.url_name, args=(self.model.pk,))

        super().setUp()

    def test_get_user(self):
        self.perform_get(user=self.model.user)

        self.assertStatus(status.HTTP_200_OK)

        for included in self.included:
            self.assertIncluded(included)

        self.assertIncluded('document')
        self.assertAttribute('answer')

    def test_get_owner(self):
        self.perform_get(user=self.activity.owner)

        self.assertStatus(status.HTTP_200_OK)

        for included in self.included:
            self.assertIncluded(included)

        self.assertIncluded('document')
        self.assertAttribute('answer')

    def test_get_other_user(self):
        self.perform_get(user=BlueBottleUserFactory.create())

        self.assertStatus(status.HTTP_200_OK)

        for included in self.included:
            self.assertIncluded(included)

        self.assertNotIncluded('document')
        self.assertAttribute('answer', None)

    def test_get_anonymous(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)

        for included in self.included:
            self.assertIncluded(included)

        self.assertNotIncluded('document')
        self.assertAttribute('answer', None)

    def test_get_anonymous_closed_site(self):
        with self.closed_site():
            self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_update(self):
        self.perform_update(
            {'answer': 'updated answer'},
            user=self.model.user
        )
        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('answer', 'updated answer')

    def test_update_user(self):
        current_user = self.model.user
        self.perform_update(
            {'user': BlueBottleUserFactory.create()},
            user=self.model.user
        )
        self.assertStatus(status.HTTP_200_OK)
        self.assertRelationship('user', [current_user])

    def test_update_owner(self):
        self.perform_update(
            {'answer': 'updated answer'},
            user=self.model.user
        )
        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('answer', 'updated answer')

    def test_update_other_user(self):
        self.perform_update(
            {'answer': 'updated answer'},
            user=self.user
        )
        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_update_anonymous(self):
        self.perform_update(
            {'answer': 'updated answer'},
        )
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)


class TimeBasedRegistrationTransitionListAPITestCase:
    fields = ['resource', 'transition']

    def setUp(self):
        self.activity = self.activity_factory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
            review=True
        )
        self.registration = self.factory.create(activity=self.activity)
        self.url = reverse(self.url_name)

        self.defaults = {
            'resource': self.registration,
            'transition': 'accept',
        }
        super().setUp()

    def test_accept(self):
        self.perform_create(user=self.activity.owner)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertIncluded('resource', self.registration)

        self.registration.refresh_from_db()
        self.assertEqual(self.defaults['resource'].status, 'accepted')

    def test_accept_yourself(self):
        self.perform_create(user=self.registration.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_reject(self):
        self.defaults['transition'] = 'reject'
        self.perform_create(user=self.activity.owner)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertIncluded('resource', self.registration)

        self.registration.refresh_from_db()
        self.assertEqual(self.defaults['resource'].status, 'rejected')

    def test_accept_other_user(self):
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.registration.refresh_from_db()

        self.assertEqual(self.defaults['resource'].status, 'new')

    def test_accept_no_user(self):
        self.perform_create()
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.registration.refresh_from_db()
        self.assertEqual(self.defaults['resource'].status, 'new')


class TimeBasedParticipantRelatedListAPITestCase:
    def setUp(self):
        self.activity = self.activity_factory.create(
            **self.activity_defaults,
            review_title='document',
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
        )
        self.factory.create_batch(5, activity=self.activity, status='succeeded')
        self.factory.create_batch(5, activity=self.activity, status='withdrawn')

        self.url = reverse(self.url_name, args=(self.activity.pk,))

        super().setUp()

    def test_get(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(10)

        self.assertTrue(
            all(
                participant['meta']['current-status']['value'] in ('succeeded', 'withdrawn')
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
                participant['meta']['current-status']['value'] in ('succeeded', 'withdrawn')
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
                participant['meta']['current-status']['value'] == 'succeeded'
                for participant in self.response.json()['data']
            )
        )

    def test_get_user_hide_first_name(self):
        self.factory.create(
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

    def test_get_anonymous(self):
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)

        self.assertTotal(5)

        self.assertTrue(
            all(
                participant['meta']['current-status']['value'] == 'succeeded'
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


class TimeBasedParticipantDetailAPITestCase:
    included = ['user', 'activity']

    def setUp(self):
        self.activity = self.activity_factory.create(
            **self.activity_defaults,
            review_title='document',
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
        )
        self.defaults = {
            'activity': self.activity
        }
        self.participant = self.factory.create(**self.defaults)
        self.url = reverse(self.url_name, args=(self.participant.pk,))

        super().setUp()

    def test_get_user(self):
        self.perform_get(user=self.participant.user)

        self.assertStatus(status.HTTP_200_OK)

        for included in self.included:
            self.assertIncluded(included)

    def test_get_owner(self):
        self.perform_get(user=self.activity.owner)

        self.assertStatus(status.HTTP_200_OK)

        for included in self.included:
            self.assertIncluded(included)

    def test_get_other_user(self):
        self.perform_get(user=BlueBottleUserFactory.create())

        self.assertStatus(status.HTTP_200_OK)

        for included in self.included:
            self.assertIncluded(included)

    def test_get_anonymous(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)

        for included in self.included:
            self.assertIncluded(included)

    def test_get_anonymous_closed_site(self):
        with self.closed_site():
            self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)


class TimeBasedParticipantTransitionListAPITestCase:
    fields = ['resource', 'transition']

    def setUp(self):
        self.activity = self.activity_factory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            review=False,
            **self.activity_defaults
        )
        self.participant = self.factory.create(activity=self.activity)
        self.url = reverse(self.url_name)

        self.defaults = {
            'resource': self.participant,
            'transition': 'withdraw',
        }
        super().setUp()

    def test_transition(self):
        self.perform_create(user=self.activity.owner)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertIncluded('resource', self.participant)

        self.participant.refresh_from_db()
        self.assertEqual(self.defaults['resource'].status, 'removed')

    def test_transition_yourself(self):
        self.perform_create(user=self.participant.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_transition_other_user(self):
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.participant.refresh_from_db()

        self.assertEqual(self.defaults['resource'].status, self.expected_status)

    def test_transition_no_user(self):
        self.perform_create()
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.participant.refresh_from_db()
        self.assertEqual(self.defaults['resource'].status, self.expected_status)


class TimeBasedActivityAPIExportTestCase:
    def setUp(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_participant_exports = True
        initiative_settings.save()

        self.activity = self.factory.create(
            **self.activity_defaults,
            review_title='document',
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
        )
        self.participant_factory.create_batch(4, activity=self.activity)

        response = self.client.get(
            reverse(self.url_name, args=(self.activity.pk, )),
            HTTP_AUTHORIZATION="JWT {0}".format(self.activity.owner.get_jwt_token())
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.url = data['attributes']['participants-export-url']['url']

    def test_get(self):
        self.perform_get(user=self.activity.owner)

        self.assertStatus(status.HTTP_200_OK)

        workbook = load_workbook(filename=BytesIO(self.response.content))
        self.assertEqual(len(workbook.worksheets), 1)

        sheet = workbook.get_active_sheet()

        sheet = workbook.get_active_sheet()

        self.assertEqual(
            tuple(sheet.values)[0],
            ('Email', 'Name', 'Registration Date', 'Status', 'Registration answer', )
        )

    def test_get_incorrect_signature(self):
        self.url = self.url + '111'
        self.perform_get(user=self.activity.owner)

        self.assertStatus(status.HTTP_404_NOT_FOUND)
