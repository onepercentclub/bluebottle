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
    ScheduleActivityFactory,
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
    Interest detail is gated by ResourceOwnerPermission, so cross-user
    access is denied.
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
