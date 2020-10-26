from datetime import timedelta

from django.utils.timezone import now

from bluebottle.time_based.tests.factories import (
    OnADateActivityFactory, WithADeadlineActivityFactory, OngoingActivityFactory,
    ApplicationFactory
)
from bluebottle.activities.models import Organizer
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class TimeBasedActivityTriggerTestCase():
    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.factory._meta.model.__name__.lower()]
        )

        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = self.factory.create(initiative=self.initiative, review=False)

    def test_initial(self):
        organizer = self.activity.contributions.instance_of(Organizer).get()
        self.assertEqual(organizer.status, 'new')

    def test_delete(self):
        self.activity.states.delete(save=True)
        organizer = self.activity.contributions.instance_of(Organizer).get()
        self.assertEqual(organizer.status, 'failed')

    def test_reject(self):
        self.initiative.states.submit(save=True)
        self.activity.states.submit()
        self.activity.states.reject(save=True)
        organizer = self.activity.contributions.instance_of(Organizer).get()
        self.assertEqual(organizer.status, 'failed')

    def test_submit_initiative(self):
        self.initiative.states.submit(save=True)
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'submitted')

    def test_submit_initiative_already_approved(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        activity = self.factory.create(initiative=self.initiative)
        activity.states.submit(save=True)

        self.assertEqual(activity.status, 'open')

    def test_submit_initiative_not_approved(self):
        self.initiative.states.submit(save=True)

        activity = self.factory.create(initiative=self.initiative)
        activity.states.submit(save=True)

        self.assertEqual(activity.status, 'submitted')

    def test_approve_initiative(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        organizer = self.activity.contributions.instance_of(Organizer).get()
        self.assertEqual(organizer.status, 'succeeded')

    def test_change_capacity(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        ApplicationFactory.create_batch(
            self.activity.capacity - 1,
            activity=self.activity,
            status='accepted'
        )

        self.activity.capacity = self.activity.capacity - 1
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.capacity = self.activity.capacity + 1
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def change_registration_deadline(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.activity.registration_deadline = (now() - timedelta(days=1)).date()
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.registration_deadline = (now() + timedelta(days=1)).date()
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')


class OnADateActivityTriggerTestCase(TimeBasedActivityTriggerTestCase, BluebottleTestCase):
    factory = OnADateActivityFactory

    def test_change_start(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        self.activity.start = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'cancelled')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = now() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def test_change_start_with_contributions(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        ApplicationFactory.create(
            activity=self.activity,
            status='accepted'
        )
        self.assertEqual(self.activity.status, 'open')

        self.activity.start = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'succeeded')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = now() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def test_change_start_full(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        ApplicationFactory.create_batch(
            self.activity.capacity,
            activity=self.activity,
        )

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')

        self.activity.start = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'succeeded')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = now() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')


class WithADeadlineActivityTriggerTestCase(TimeBasedActivityTriggerTestCase, BluebottleTestCase):
    factory = WithADeadlineActivityFactory

    def test_change_deadline(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        self.activity.deadline = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'cancelled')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.deadline = now() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def test_change_deadline_with_contributions(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        ApplicationFactory.create(
            activity=self.activity,
            status='accepted'
        )
        self.assertEqual(self.activity.status, 'open')

        self.activity.deadline = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'succeeded')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.deadline = now() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def test_change_deadline_full(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        ApplicationFactory.create_batch(
            self.activity.capacity,
            activity=self.activity,
        )

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')

        self.activity.deadline = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'succeeded')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.deadline = now() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

    def test_change_start(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.activity.start = (now() - timedelta(days=1)).date()
        self.activity.save()

        self.assertEqual(self.activity.status, 'running')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = (now() + timedelta(days=2)).date()
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def test_change_start_after_registration_deadline(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.activity.registration_deadline = (now() - timedelta(days=4)).date()
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.start = (now() - timedelta(days=1)).date()

        self.activity.save()

        self.assertEqual(self.activity.status, 'running')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = (now() + timedelta(days=2)).date()
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

    def test_change_start_after_full(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        ApplicationFactory.create_batch(
            self.activity.capacity,
            activity=self.activity,
        )

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'full')

        self.activity.start = (now() - timedelta(days=1)).date()

        self.activity.save()

        self.assertEqual(self.activity.status, 'running')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = (now() + timedelta(days=2)).date()
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')


class OngoingActivityTriggerTestCase(TimeBasedActivityTriggerTestCase, BluebottleTestCase):
    factory = OngoingActivityFactory


class ApplicationTriggerTestCase():

    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.factory._meta.model.__name__.lower()]
        )

        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = self.factory.create(initiative=self.initiative, review=False)
        self.review_activity = self.factory.create(initiative=self.initiative, review=True)

        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()
        self.review_activity.refresh_from_db()

    def test_initial_review(self):
        application = ApplicationFactory.create(activity=self.review_activity)

        self.assertEqual(application.status, 'new')

    def test_initial_no_review(self):
        application = ApplicationFactory.create(activity=self.activity)

        self.assertEqual(application.status, 'accepted')

    def test_no_review_fill(self):
        ApplicationFactory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')

    def test_review_fill(self):
        applications = ApplicationFactory.create_batch(
            self.review_activity.capacity, activity=self.review_activity
        )
        self.review_activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        for application in applications:
            application.states.accept(save=True)

        self.review_activity.refresh_from_db()

        self.assertEqual(self.review_activity.status, 'full')

    def test_reject(self):
        applications = ApplicationFactory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')
        applications[0].states.reject(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'open')

        applications[0].states.accept(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'full')

    def test_withdraw(self):
        applications = ApplicationFactory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')

        applications[0].states.withdraw(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'open')

        applications[0].states.reapply(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'full')


class OnADateApplicationTriggerTestCase(ApplicationTriggerTestCase, BluebottleTestCase):
    factory = OnADateActivityFactory

    def test_no_review_succeed(self):
        self.activity.start = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'cancelled')

        ApplicationFactory.create(activity=self.activity)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')


class WithADeadlineApplicationTriggerTestCase(ApplicationTriggerTestCase, BluebottleTestCase):
    factory = WithADeadlineActivityFactory

    def test_no_review_succeed(self):
        self.activity.deadline = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'cancelled')

        ApplicationFactory.create(activity=self.activity)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')


class OngoingApplicationTriggerTestCase(ApplicationTriggerTestCase, BluebottleTestCase):
    factory = OngoingActivityFactory
