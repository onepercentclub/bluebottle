from datetime import date, timedelta

from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import APITestCase
from bluebottle.time_based.serializers.interests import InterestSerializer
from bluebottle.time_based.serializers import (
    DateActivitySlotSerializer,
    DeadlineActivitySerializer,
    PeriodicActivitySerializer,
    ScheduleActivitySerializer,
)
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DateParticipantFactory,
    DeadlineActivityFactory,
    DeadlineParticipantFactory,
    DeadlineRegistrationFactory,
    InterestFactory,
    PeriodicActivityFactory,
    PeriodicRegistrationFactory,
    ScheduleActivityFactory,
    ScheduleRegistrationFactory,
)


class InterestListAPITestCase(APITestCase):
    url_name = 'interest-list'
    serializer = InterestSerializer
    factory = InterestFactory
    fields = ['activity']

    def setUp(self):
        super().setUp()
        self.activity = DeadlineActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='full',
            capacity=1,
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
        )
        self.url = reverse(self.url_name)
        self.defaults = {
            'activity': self.activity,
        }

    def test_create(self):
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.user, self.user)
        self.assertEqual(self.model.activity, self.activity)
        self.assertIsNone(self.model.slot)

    def test_create_idempotent(self):
        existing = InterestFactory.create(user=self.user, activity=self.activity)
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.pk, existing.pk)

    def test_create_open_activity(self):
        self.activity.status = 'open'
        self.activity.save()
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_already_participating(self):
        DeadlineParticipantFactory.create(
            user=self.user,
            activity=self.activity,
            status='accepted',
        )
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_already_applicant(self):
        DeadlineRegistrationFactory.create(
            user=self.user,
            activity=self.activity,
            status='new',
        )
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_with_slot_on_non_date_activity(self):
        date_activity = DateActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            review=False,
        )
        slot = DateActivitySlotFactory.create(
            activity=date_activity,
            status='full',
            capacity=1,
        )
        self.fields = ['activity', 'slot']
        self.defaults = {
            'activity': self.activity,
            'slot': slot,
        }
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_multiple_users_no_cap(self):
        for _ in range(5):
            other = BlueBottleUserFactory.create()
            InterestFactory.create(user=other, activity=self.activity)
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(
            self.activity.interests.filter(slot__isnull=True).count(),
            6,
        )

    def test_create_anonymous(self):
        self.perform_create()
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_create_periodic(self):
        activity = PeriodicActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='full',
            capacity=1,
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
        )
        self.defaults = {'activity': activity}
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.activity, activity)

    def test_create_schedule(self):
        activity = ScheduleActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='full',
            capacity=1,
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
        )
        self.defaults = {'activity': activity}
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.activity, activity)

    def test_create_registration_closed_activity(self):
        self.activity.status = 'registration_closed'
        self.activity.save()
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_registration_closed_not_at_capacity(self):
        """Interest stays blocked when closed, even if capacity is free."""
        self.activity.status = 'registration_closed'
        self.activity.capacity = 10
        self.activity.save()
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_registration_closed_periodic(self):
        activity = PeriodicActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='registration_closed',
            capacity=1,
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
        )
        self.defaults = {'activity': activity}
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_registration_closed_schedule(self):
        activity = ScheduleActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='registration_closed',
            capacity=1,
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
        )
        self.defaults = {'activity': activity}
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_after_withdraw_while_registration_closed(self):
        """Freed capacity after withdraw must not reopen interest signup."""
        participant = DeadlineParticipantFactory.create(
            activity=self.activity,
            status='accepted',
        )
        self.activity.status = 'registration_closed'
        self.activity.save()

        participant.states.withdraw(save=True)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'registration_closed')

        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_idempotent_when_already_interested_and_closed(self):
        existing = InterestFactory.create(user=self.user, activity=self.activity)
        self.activity.status = 'registration_closed'
        self.activity.save()

        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.pk, existing.pk)

    def test_create_allowed_again_when_reopened_to_full(self):
        self.activity.status = 'registration_closed'
        self.activity.save()
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

        self.activity.status = 'full'
        self.activity.save()
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.activity, self.activity)


class InterestDateSlotAPITestCase(APITestCase):
    url_name = 'interest-list'
    serializer = InterestSerializer
    factory = InterestFactory
    fields = ['activity', 'slot']

    def setUp(self):
        super().setUp()
        self.activity = DateActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            review=False,
        )
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity,
            status='full',
            capacity=1,
        )
        self.url = reverse(self.url_name)
        self.defaults = {
            'activity': self.activity,
            'slot': self.slot,
        }

    def test_create(self):
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.slot, self.slot)
        self.assertEqual(self.model.activity, self.activity)

    def test_create_idempotent(self):
        existing = InterestFactory.create(
            user=self.user,
            activity=self.activity,
            slot=self.slot,
        )
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.pk, existing.pk)

    def test_create_without_slot(self):
        self.fields = ['activity']
        self.defaults = {'activity': self.activity}
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_open_slot(self):
        self.slot.status = 'open'
        self.slot.save()
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_already_participating(self):
        DateParticipantFactory.create(
            user=self.user,
            activity=self.activity,
            slot=self.slot,
            status='accepted',
        )
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_wrong_activity_for_slot(self):
        other_activity = DateActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            review=False,
        )
        self.defaults = {
            'activity': other_activity,
            'slot': self.slot,
        }
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_scoped_per_slot(self):
        other_slot = DateActivitySlotFactory.create(
            activity=self.activity,
            status='full',
            capacity=1,
        )
        InterestFactory.create(
            user=self.user,
            activity=self.activity,
            slot=self.slot,
        )
        self.defaults = {
            'activity': self.activity,
            'slot': other_slot,
        }
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.slot, other_slot)
        self.assertEqual(
            self.activity.interests.filter(user=self.user).count(),
            2,
        )

    def test_create_registration_closed_slot(self):
        self.slot.status = 'registration_closed'
        self.slot.save()
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_when_activity_registration_closed(self):
        self.activity.status = 'registration_closed'
        self.activity.save()
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)


class InterestDetailAPITestCase(APITestCase):
    url_name = 'interest-detail'
    serializer = InterestSerializer
    factory = InterestFactory

    def setUp(self):
        super().setUp()
        self.activity = DeadlineActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='full',
            capacity=1,
            review=False,
        )
        self.model = InterestFactory.create(user=self.user, activity=self.activity)
        self.url = reverse(self.url_name, args=(self.model.pk,))

    def test_get(self):
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)

    def test_get_other_user(self):
        other = BlueBottleUserFactory.create()
        self.perform_get(user=other)
        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_delete(self):
        self.perform_delete(user=self.user)
        self.assertStatus(status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            self.factory._meta.model.objects.filter(pk=self.model.pk).exists()
        )

    def test_delete_other_user(self):
        other = BlueBottleUserFactory.create()
        self.perform_delete(user=other)
        self.assertStatus(status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            self.factory._meta.model.objects.filter(pk=self.model.pk).exists()
        )


class InterestPermissionAPITestCase(APITestCase):
    """
    Authenticated members only receive *_own_* interest API permissions.
    Unrelated users still cannot access foreign interests; activity managers
    and staff can delete via RelatedActivityOwnerPermission / IsAdminPermission.
    """
    url_name = 'interest-detail'
    serializer = InterestSerializer
    factory = InterestFactory

    def setUp(self):
        super().setUp()
        self.activity = DeadlineActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='full',
            capacity=1,
            review=False,
        )
        self.model = InterestFactory.create(user=self.user, activity=self.activity)
        self.url = reverse(self.url_name, args=(self.model.pk,))
        self.other = BlueBottleUserFactory.create()

    def test_authenticated_group_has_only_own_interest_api_permissions(self):
        authenticated = Group.objects.get(name='Authenticated')
        codenames = set(
            authenticated.permissions.filter(
                content_type__app_label='time_based',
                codename__endswith='_interest',
            ).values_list('codename', flat=True)
        )
        self.assertTrue(
            {
                'api_add_own_interest',
                'api_read_own_interest',
                'api_delete_own_interest',
            }.issubset(codenames),
            codenames,
        )
        self.assertFalse(
            {
                'api_read_interest',
                'api_add_interest',
                'api_change_interest',
                'api_delete_interest',
            } & codenames,
            codenames,
        )

    def test_other_authenticated_user_lacks_global_delete_perm(self):
        self.assertFalse(self.other.has_perm('time_based.api_delete_interest'))
        self.assertTrue(self.other.has_perm('time_based.api_delete_own_interest'))

    def test_other_authenticated_user_cannot_delete_foreign_interest(self):
        self.perform_delete(user=self.other)
        self.assertStatus(status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            self.factory._meta.model.objects.filter(pk=self.model.pk).exists()
        )

    def test_other_authenticated_user_cannot_get_foreign_interest(self):
        self.perform_get(user=self.other)
        self.assertStatus(status.HTTP_403_FORBIDDEN)


class DeadlineActivityMyInterestAPITestCase(APITestCase):
    url_name = 'deadline-detail'
    serializer = DeadlineActivitySerializer
    factory = DeadlineActivityFactory

    def setUp(self):
        super().setUp()
        self.model = DeadlineActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='full',
            capacity=1,
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
        )
        self.url = reverse(self.url_name, args=(self.model.pk,))

    def test_get_with_interest(self):
        interest = InterestFactory.create(user=self.user, activity=self.model)
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertIncluded('my-interest', interest)

    def test_get_without_interest(self):
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertIsNone(
            self.response.json()['data']['relationships']['my-interest']['data']
        )

    def test_get_anonymous(self):
        InterestFactory.create(user=self.user, activity=self.model)
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)
        self.assertIsNone(
            self.response.json()['data']['relationships']['my-interest']['data']
        )

    def test_my_interest_persists_after_registration_closed(self):
        interest = InterestFactory.create(user=self.user, activity=self.model)
        self.model.status = 'registration_closed'
        self.model.save()

        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertIncluded('my-interest', interest)


class PeriodicActivityMyInterestAPITestCase(APITestCase):
    url_name = 'periodic-detail'
    serializer = PeriodicActivitySerializer
    factory = PeriodicActivityFactory

    def setUp(self):
        super().setUp()
        self.model = PeriodicActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='full',
            capacity=1,
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
        )
        self.url = reverse(self.url_name, args=(self.model.pk,))

    def test_get_with_interest(self):
        interest = InterestFactory.create(user=self.user, activity=self.model)
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertIncluded('my-interest', interest)


class ScheduleActivityMyInterestAPITestCase(APITestCase):
    url_name = 'schedule-detail'
    serializer = ScheduleActivitySerializer
    factory = ScheduleActivityFactory

    def setUp(self):
        super().setUp()
        self.model = ScheduleActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='full',
            capacity=1,
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
        )
        self.url = reverse(self.url_name, args=(self.model.pk,))

    def test_get_with_interest(self):
        interest = InterestFactory.create(user=self.user, activity=self.model)
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertIncluded('my-interest', interest)


class DateSlotMyInterestAPITestCase(APITestCase):
    url_name = 'date-slot-detail'
    serializer = DateActivitySlotSerializer
    factory = DateActivitySlotFactory

    def setUp(self):
        super().setUp()
        self.activity = DateActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            review=False,
        )
        self.model = DateActivitySlotFactory.create(
            activity=self.activity,
            status='full',
            capacity=1,
        )
        self.url = reverse(self.url_name, args=(self.model.pk,))

    def test_get_with_interest(self):
        interest = InterestFactory.create(
            user=self.user,
            activity=self.activity,
            slot=self.model,
        )
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertIncluded('my-interest', interest)

    def test_get_without_interest(self):
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertIsNone(
            self.response.json()['data']['relationships']['my-interest']['data']
        )

    def test_my_interest_persists_after_registration_closed(self):
        interest = InterestFactory.create(
            user=self.user,
            activity=self.activity,
            slot=self.model,
        )
        self.model.status = 'registration_closed'
        self.model.save()
        self.activity.status = 'registration_closed'
        self.activity.save()

        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertIncluded('my-interest', interest)


class InterestDeleteOnJoinAPITestCase(APITestCase):
    """Joining or applying deletes the matching Interest row entirely."""

    def test_deadline_registration_deletes_interest(self):
        activity = DeadlineActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            capacity=2,
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
        )
        user = BlueBottleUserFactory.create()
        interest = InterestFactory.create(user=user, activity=activity)

        DeadlineRegistrationFactory.create(
            user=user,
            activity=activity,
        )

        self.assertFalse(
            InterestFactory._meta.model.objects.filter(pk=interest.pk).exists()
        )

    def test_deadline_registration_with_review_still_deletes_interest(self):
        activity = DeadlineActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            capacity=2,
            review=True,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
        )
        user = BlueBottleUserFactory.create()
        interest = InterestFactory.create(user=user, activity=activity)

        registration = DeadlineRegistrationFactory.create(
            user=user,
            activity=activity,
        )

        self.assertEqual(registration.status, 'new')
        self.assertFalse(
            InterestFactory._meta.model.objects.filter(pk=interest.pk).exists()
        )

    def test_date_participant_deletes_slot_interest(self):
        activity = DateActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            review=False,
        )
        slot = DateActivitySlotFactory.create(
            activity=activity,
            status='open',
            capacity=2,
        )
        user = BlueBottleUserFactory.create()
        interest = InterestFactory.create(
            user=user,
            activity=activity,
            slot=slot,
        )

        DateParticipantFactory.create(
            user=user,
            activity=activity,
            slot=slot,
        )

        self.assertFalse(
            InterestFactory._meta.model.objects.filter(pk=interest.pk).exists()
        )

    def test_date_participant_does_not_delete_other_slot_interest(self):
        activity = DateActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            review=False,
        )
        slot = DateActivitySlotFactory.create(
            activity=activity,
            status='open',
            capacity=2,
        )
        other_slot = DateActivitySlotFactory.create(
            activity=activity,
            status='full',
            capacity=1,
        )
        user = BlueBottleUserFactory.create()
        other_interest = InterestFactory.create(
            user=user,
            activity=activity,
            slot=other_slot,
        )

        DateParticipantFactory.create(
            user=user,
            activity=activity,
            slot=slot,
        )

        self.assertTrue(
            InterestFactory._meta.model.objects.filter(pk=other_interest.pk).exists()
        )

    def test_schedule_registration_deletes_interest(self):
        activity = ScheduleActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            capacity=2,
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
        )
        user = BlueBottleUserFactory.create()
        interest = InterestFactory.create(user=user, activity=activity)

        ScheduleRegistrationFactory.create(
            user=user,
            activity=activity,
        )

        self.assertFalse(
            InterestFactory._meta.model.objects.filter(pk=interest.pk).exists()
        )

    def test_periodic_registration_deletes_interest(self):
        activity = PeriodicActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            capacity=2,
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
        )
        user = BlueBottleUserFactory.create()
        interest = InterestFactory.create(user=user, activity=activity)

        PeriodicRegistrationFactory.create(
            user=user,
            activity=activity,
        )

        self.assertFalse(
            InterestFactory._meta.model.objects.filter(pk=interest.pk).exists()
        )

    def test_date_participant_with_review_still_deletes_interest(self):
        activity = DateActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            review=True,
        )
        slot = DateActivitySlotFactory.create(
            activity=activity,
            status='open',
            capacity=2,
        )
        user = BlueBottleUserFactory.create()
        interest = InterestFactory.create(
            user=user,
            activity=activity,
            slot=slot,
        )

        participant = DateParticipantFactory.create(
            user=user,
            activity=activity,
            slot=slot,
        )

        self.assertEqual(participant.status, 'new')
        self.assertFalse(
            InterestFactory._meta.model.objects.filter(pk=interest.pk).exists()
        )


class InterestLifecycleIsolationTestCase(APITestCase):
    """Interest survives activity cancel/succeed; only explicit removals delete it."""

    def test_cancel_activity_keeps_interest(self):
        activity = DeadlineActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='full',
            capacity=1,
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
        )
        interest = InterestFactory.create(
            user=BlueBottleUserFactory.create(),
            activity=activity,
        )

        activity.states.cancel(save=True)

        self.assertEqual(activity.status, 'cancelled')
        self.assertTrue(
            InterestFactory._meta.model.objects.filter(pk=interest.pk).exists()
        )

    def test_succeed_activity_keeps_interest(self):
        activity = DeadlineActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            capacity=2,
            review=False,
            start=date.today() - timedelta(days=10),
            deadline=date.today() - timedelta(days=1),
        )
        DeadlineParticipantFactory.create(
            activity=activity,
            status='accepted',
        )
        interest = InterestFactory.create(
            user=BlueBottleUserFactory.create(),
            activity=activity,
        )

        activity.states.succeed(save=True)

        self.assertEqual(activity.status, 'succeeded')
        self.assertTrue(
            InterestFactory._meta.model.objects.filter(pk=interest.pk).exists()
        )

    def test_registration_deadline_lock_keeps_interest(self):
        """
        On this branch, a passed registration deadline locks an open activity
        with participants to full. Interest must survive that transition.
        """
        activity = DeadlineActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            capacity=2,
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
            registration_deadline=date.today() - timedelta(days=1),
        )
        DeadlineParticipantFactory.create(
            activity=activity,
            status='accepted',
        )
        interest = InterestFactory.create(
            user=BlueBottleUserFactory.create(),
            activity=activity,
        )

        activity.states.lock(save=True)

        self.assertEqual(activity.status, 'full')
        self.assertTrue(
            InterestFactory._meta.model.objects.filter(pk=interest.pk).exists()
        )

    def test_registration_deadline_expire_keeps_interest(self):
        """
        A passed registration deadline with no participants expires the
        activity. Interest must survive that transition too.
        """
        activity = DeadlineActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            capacity=2,
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
            registration_deadline=date.today() - timedelta(days=1),
        )
        interest = InterestFactory.create(
            user=BlueBottleUserFactory.create(),
            activity=activity,
        )

        activity.states.expire(save=True)

        self.assertEqual(activity.status, 'expired')
        self.assertTrue(
            InterestFactory._meta.model.objects.filter(pk=interest.pk).exists()
        )


class InterestManagerDeleteAPITestCase(APITestCase):
    url_name = 'interest-detail'
    serializer = InterestSerializer
    factory = InterestFactory

    def setUp(self):
        super().setUp()
        initiative = InitiativeFactory.create(status='approved')
        self.activity = DeadlineActivityFactory.create(
            initiative=initiative,
            status='full',
            capacity=1,
            review=False,
            owner=initiative.owner,
        )
        self.interested_user = BlueBottleUserFactory.create()
        self.model = InterestFactory.create(
            user=self.interested_user,
            activity=self.activity,
        )
        self.url = reverse(self.url_name, args=(self.model.pk,))

    def test_activity_owner_can_delete_interest(self):
        self.perform_delete(user=self.activity.owner)
        self.assertStatus(status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            self.factory._meta.model.objects.filter(pk=self.model.pk).exists()
        )

    def test_activity_manager_can_delete_interest(self):
        manager = BlueBottleUserFactory.create()
        self.activity.initiative.activity_managers.add(manager)

        self.perform_delete(user=manager)
        self.assertStatus(status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            self.factory._meta.model.objects.filter(pk=self.model.pk).exists()
        )

    def test_staff_can_delete_interest(self):
        staff = BlueBottleUserFactory.create(is_staff=True)
        self.perform_delete(user=staff)
        self.assertStatus(status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            self.factory._meta.model.objects.filter(pk=self.model.pk).exists()
        )

    def test_unrelated_user_still_cannot_delete(self):
        other = BlueBottleUserFactory.create()
        self.perform_delete(user=other)
        self.assertStatus(status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            self.factory._meta.model.objects.filter(pk=self.model.pk).exists()
        )


class InterestSlotManagerDeleteAPITestCase(APITestCase):
    url_name = 'interest-detail'
    serializer = InterestSerializer
    factory = InterestFactory

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
        self.interested_user = BlueBottleUserFactory.create()
        self.model = InterestFactory.create(
            user=self.interested_user,
            activity=self.activity,
            slot=self.slot,
        )
        self.url = reverse(self.url_name, args=(self.model.pk,))

    def test_activity_owner_can_delete_slot_interest(self):
        self.perform_delete(user=self.activity.owner)
        self.assertStatus(status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            self.factory._meta.model.objects.filter(pk=self.model.pk).exists()
        )

    def test_activity_manager_can_delete_slot_interest(self):
        manager = BlueBottleUserFactory.create()
        self.activity.initiative.activity_managers.add(manager)

        self.perform_delete(user=manager)
        self.assertStatus(status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            self.factory._meta.model.objects.filter(pk=self.model.pk).exists()
        )

    def test_staff_can_delete_slot_interest(self):
        staff = BlueBottleUserFactory.create(is_staff=True)
        self.perform_delete(user=staff)
        self.assertStatus(status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            self.factory._meta.model.objects.filter(pk=self.model.pk).exists()
        )


class DeadlineInterestRelatedListAPITestCase(APITestCase):
    url_name = 'deadline-interests'
    serializer = InterestSerializer
    factory = InterestFactory
    activity_factory = DeadlineActivityFactory
    activity_serializer = DeadlineActivitySerializer

    def setUp(self):
        super().setUp()
        initiative = InitiativeFactory.create(status='approved')
        self.activity = self.activity_factory.create(
            initiative=initiative,
            status='full',
            capacity=1,
            review=False,
            owner=initiative.owner,
        )
        self.interests = InterestFactory.create_batch(
            3, activity=self.activity, slot=None
        )
        date_activity = DateActivityFactory.create(
            initiative=initiative,
        )
        InterestFactory.create(
            activity=date_activity,
            slot=DateActivitySlotFactory.create(
                activity=date_activity,
                status='full',
            ),
        )
        self.url = reverse(self.url_name, args=(self.activity.pk,))

    def test_manager_can_list_interests(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(3)

    def test_activity_manager_can_list_interests(self):
        manager = BlueBottleUserFactory.create()
        self.activity.initiative.activity_managers.add(manager)

        self.perform_get(user=manager)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(3)

    def test_unrelated_user_cannot_list_interests(self):
        other = BlueBottleUserFactory.create()
        self.perform_get(user=other)
        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_list_interests(self):
        self.perform_get(user=None)
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_list_works_when_activity_succeeded(self):
        self.activity.status = 'succeeded'
        self.activity.save()

        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(3)

    def test_list_works_when_activity_cancelled(self):
        self.activity.status = 'cancelled'
        self.activity.save()

        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(3)

    def test_activity_includes_interests_link_for_manager(self):
        self.url = reverse('deadline-detail', args=(self.activity.pk,))
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        interests = self.response.json()['data']['relationships']['interests']['links']
        self.assertEqual(interests['related']['meta']['count'], 3)
        self.assertIn(
            reverse(self.url_name, args=(self.activity.pk,)),
            interests['related']['href'],
        )

    def test_activity_hides_interests_link_for_member(self):
        member = BlueBottleUserFactory.create()
        self.url = reverse('deadline-detail', args=(self.activity.pk,))
        self.perform_get(user=member)
        self.assertStatus(status.HTTP_200_OK)
        self.assertNotIn(
            'interests',
            self.response.json()['data']['relationships'],
        )

    def test_list_invalid_activity_returns_404(self):
        self.url = reverse(self.url_name, args=(999999,))
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_404_NOT_FOUND)

    def test_staff_can_list_interests(self):
        staff = BlueBottleUserFactory.create(is_staff=True)
        self.perform_get(user=staff)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(3)

    def test_list_works_when_activity_expired(self):
        self.activity.status = 'expired'
        self.activity.save()

        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(3)

    def test_list_includes_user(self):
        self.perform_get(user=self.activity.owner, query={'include': 'user'})
        self.assertStatus(status.HTTP_200_OK)
        self.assertTrue(
            any(
                item['type'] == 'members'
                for item in self.response.json().get('included', [])
            )
        )


class ScheduleInterestRelatedListAPITestCase(APITestCase):
    url_name = 'schedule-interests'
    serializer = InterestSerializer
    factory = InterestFactory

    def setUp(self):
        super().setUp()
        initiative = InitiativeFactory.create(status='approved')
        self.activity = ScheduleActivityFactory.create(
            initiative=initiative,
            status='full',
            capacity=1,
            review=False,
            owner=initiative.owner,
        )
        InterestFactory.create_batch(2, activity=self.activity, slot=None)
        self.url = reverse(self.url_name, args=(self.activity.pk,))

    def test_manager_can_list_interests(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(2)


class PeriodicInterestRelatedListAPITestCase(APITestCase):
    url_name = 'periodic-interests'
    serializer = InterestSerializer
    factory = InterestFactory

    def setUp(self):
        super().setUp()
        initiative = InitiativeFactory.create(status='approved')
        self.activity = PeriodicActivityFactory.create(
            initiative=initiative,
            status='full',
            capacity=1,
            review=False,
            owner=initiative.owner,
        )
        InterestFactory.create_batch(2, activity=self.activity, slot=None)
        self.url = reverse(self.url_name, args=(self.activity.pk,))

    def test_manager_can_list_interests(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(2)


class DateActivityInterestRelatedListAPITestCase(APITestCase):
    url_name = 'date-interests'
    serializer = InterestSerializer
    factory = InterestFactory

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
        InterestFactory.create_batch(2, activity=self.activity, slot=self.slot)
        InterestFactory.create(activity=self.activity, slot=None)
        self.url = reverse(self.url_name, args=(self.activity.pk,))

    def test_manager_can_list_all_interests(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(3)


class DateSlotInterestRelatedListAPITestCase(APITestCase):
    url_name = 'date-slot-interests'
    serializer = InterestSerializer
    factory = InterestFactory

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
        self.url = reverse(self.url_name, args=(self.slot.pk,))

    def test_manager_can_list_slot_interests(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(2)

    def test_unrelated_user_cannot_list_slot_interests(self):
        other = BlueBottleUserFactory.create()
        self.perform_get(user=other)
        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_slot_includes_interests_link_for_manager(self):
        self.url = reverse('date-slot-detail', args=(self.slot.pk,))
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        interests = self.response.json()['data']['relationships']['interests']['links']
        self.assertEqual(interests['related']['meta']['count'], 2)

    def test_list_invalid_slot_returns_404(self):
        self.url = reverse(self.url_name, args=(999999,))
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_404_NOT_FOUND)
