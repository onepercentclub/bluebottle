from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import APITestCase
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DateParticipantFactory,
    DateRegistrationFactory,
    DeadlineActivityFactory,
    DeadlineParticipantFactory,
    DeadlineRegistrationFactory,
    InterestFactory,
    PeriodicActivityFactory,
    PeriodicParticipantFactory,
    PeriodicRegistrationFactory,
    ScheduleActivityFactory,
    ScheduleParticipantFactory,
    ScheduleRegistrationFactory,
)


class ActivityRelatedLinkFieldsMixin:
    """
    Verify contributors, registrations and interests relationship links on
    activity detail responses (link-only fields without many=True).
    """

    activity_factory = None
    detail_url_name = None
    contributors_list_url_name = None
    registrations_list_url_name = None
    interests_list_url_name = None
    participant_factory = None
    registration_factory = None
    activity_kwargs = None

    def setUp(self):
        super().setUp()
        initiative = InitiativeFactory.create(status='approved')
        kwargs = {
            'initiative': initiative,
            'status': 'open',
            'review': False,
            'owner': initiative.owner,
        }
        if self.activity_kwargs:
            kwargs.update(self.activity_kwargs)

        self.activity = self.activity_factory.create(**kwargs)
        self.before_participant_setup()
        participant_kwargs = {'activity': self.activity, 'status': 'succeeded'}
        participant_kwargs.update(self.get_participant_kwargs())
        self.participant_factory.create(**participant_kwargs)
        self.registration_factory.create(
            activity=self.activity,
            status='new',
        )
        self.registration_factory.create(
            activity=self.activity,
            status='accepted',
        )
        self.registration_factory.create(
            activity=self.activity,
            status='rejected',
        )
        self.interests = InterestFactory.create_batch(
            2, activity=self.activity, slot=None
        )
        self.url = reverse(self.detail_url_name, args=(self.activity.pk,))

    def before_participant_setup(self):
        pass

    def get_participant_kwargs(self):
        return {}

    def _relationships(self):
        return self.response.json()['data']['relationships']

    def test_contributors_link_structure_and_count(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        links = self._relationships()['contributors']['links']
        self.assertIsInstance(links['related'], str)
        self.assertIn(
            reverse(self.contributors_list_url_name, args=(self.activity.pk,)),
            links['related'],
        )
        self.assertEqual(links['active']['meta']['count'], 1)

    def test_registrations_link_structure_and_counts(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        links = self._relationships()['registrations']['links']
        self.assertIsInstance(links['related'], str)
        self.assertIn(
            reverse(self.registrations_list_url_name, args=(self.activity.pk,)),
            links['related'],
        )
        self.assertEqual(links['new']['meta']['count'], 1)
        self.assertEqual(links['accepted']['meta']['count'], 1)
        self.assertEqual(links['rejected']['meta']['count'], 1)

    def test_registrations_filtered_link_is_usable(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        href = self._relationships()['registrations']['links']['accepted']['href']
        response = self.client.get(href, user=self.activity.owner)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 1)

    def test_interests_link_for_manager(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        links = self._relationships()['interests']['links']
        self.assertEqual(links['related']['meta']['count'], 2)
        self.assertIn(
            reverse(self.interests_list_url_name, args=(self.activity.pk,)),
            links['related']['href'],
        )

    def test_interests_link_hidden_for_member(self):
        member = BlueBottleUserFactory.create()
        self.perform_get(user=member)
        self.assertStatus(status.HTTP_200_OK)
        self.assertNotIn('interests', self._relationships())

    def test_interests_link_for_staff(self):
        staff = BlueBottleUserFactory.create(is_staff=True)
        self.perform_get(user=staff)
        self.assertStatus(status.HTTP_200_OK)
        self.assertIn('interests', self._relationships())

    def test_interests_related_link_is_usable(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        href = self._relationships()['interests']['links']['related']['href']
        response = self.client.get(href, user=self.activity.owner)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)


class DeadlineActivityRelatedLinkFieldsTestCase(
    ActivityRelatedLinkFieldsMixin, APITestCase
):
    activity_factory = DeadlineActivityFactory
    detail_url_name = 'deadline-detail'
    contributors_list_url_name = 'deadline-participants'
    registrations_list_url_name = 'related-deadline-registrations'
    interests_list_url_name = 'deadline-interests'
    participant_factory = DeadlineParticipantFactory
    registration_factory = DeadlineRegistrationFactory
    activity_kwargs = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class ScheduleActivityRelatedLinkFieldsTestCase(
    ActivityRelatedLinkFieldsMixin, APITestCase
):
    activity_factory = ScheduleActivityFactory
    detail_url_name = 'schedule-detail'
    contributors_list_url_name = 'schedule-participants'
    registrations_list_url_name = 'related-schedule-registrations'
    interests_list_url_name = 'schedule-interests'
    participant_factory = ScheduleParticipantFactory
    registration_factory = ScheduleRegistrationFactory
    activity_kwargs = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class PeriodicActivityRelatedLinkFieldsTestCase(
    ActivityRelatedLinkFieldsMixin, APITestCase
):
    activity_factory = PeriodicActivityFactory
    detail_url_name = 'periodic-detail'
    contributors_list_url_name = 'periodic-participants'
    registrations_list_url_name = 'related-periodic-registrations'
    interests_list_url_name = 'periodic-interests'
    participant_factory = PeriodicParticipantFactory
    registration_factory = PeriodicRegistrationFactory
    activity_kwargs = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }


class DateActivityRelatedLinkFieldsTestCase(
    ActivityRelatedLinkFieldsMixin, APITestCase
):
    activity_factory = DateActivityFactory
    detail_url_name = 'date-detail'
    contributors_list_url_name = 'date-participants'
    registrations_list_url_name = 'related-date-registrations'
    interests_list_url_name = 'date-interests'
    participant_factory = DateParticipantFactory
    registration_factory = DateRegistrationFactory

    def before_participant_setup(self):
        self.slot = DateActivitySlotFactory.create(activity=self.activity)

    def get_participant_kwargs(self):
        return {'slot': self.slot}

    def setUp(self):
        super().setUp()
        InterestFactory.create(activity=self.activity, slot=self.slot)

    def test_interests_link_for_manager(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        links = self._relationships()['interests']['links']
        self.assertEqual(links['related']['meta']['count'], 3)

    def test_interests_related_link_is_usable(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        href = self._relationships()['interests']['links']['related']['href']
        response = self.client.get(href, user=self.activity.owner)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 3)

    def test_slots_link_structure(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        links = self._relationships()['slots']['links']
        self.assertIsInstance(links['related'], str)
        self.assertIn(
            reverse('related-date-slots', args=(self.activity.pk,)),
            links['related'],
        )
        expected = self.activity.slots.exclude(
            status__in=['draft', 'cancelled']
        ).count()
        self.assertEqual(links['total']['meta']['count'], expected)

class DateSlotRelatedLinkFieldsTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        initiative = InitiativeFactory.create(status='approved')
        self.activity = DateActivityFactory.create(
            initiative=initiative,
            status='open',
            review=False,
            owner=initiative.owner,
        )
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity,
            status='full',
            capacity=1,
        )
        self.interests = InterestFactory.create_batch(
            2, activity=self.activity, slot=self.slot
        )
        InterestFactory.create(activity=self.activity, slot=None)
        self.url = reverse('date-slot-detail', args=(self.slot.pk,))

    def test_slot_includes_interests_link_for_manager(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        links = self.response.json()['data']['relationships']['interests']['links']
        self.assertEqual(links['related']['meta']['count'], 2)
        self.assertIn(
            reverse('date-slot-interests', args=(self.slot.pk,)),
            links['related']['href'],
        )

    def test_slot_hides_interests_link_for_member(self):
        member = BlueBottleUserFactory.create()
        self.perform_get(user=member)
        self.assertStatus(status.HTTP_200_OK)
        self.assertNotIn(
            'interests',
            self.response.json()['data']['relationships'],
        )

    def test_slot_interests_related_link_is_usable(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)

        href = self.response.json()['data']['relationships']['interests']['links']['related']['href']
        response = self.client.get(href, user=self.activity.owner)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)
