from datetime import timedelta, date

from django.utils.timezone import now

from bluebottle.time_based.tests.factories import (
    DateActivityFactory, PeriodActivityFactory,
    OnADateApplicationFactory, PeriodApplicationFactory
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

        self.application_factory.create_batch(
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

        self.activity.registration_deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.registration_deadline = date.today() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')


class DateActivityTriggerTestCase(TimeBasedActivityTriggerTestCase, BluebottleTestCase):
    factory = DateActivityFactory
    application_factory = OnADateApplicationFactory

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

        self.accepted = self.application_factory.create(
            activity=self.activity,
        )

        self.rejected = self.application_factory.create(
            activity=self.activity,
        )
        self.rejected.states.reject(save=True)

        self.assertEqual(self.activity.status, 'open')

        self.activity.start = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'succeeded')

        self.assertEqual(
            self.rejected.contribution_values.get().status, 'failed'
        )

        self.assertEqual(
            self.accepted.contribution_values.get().status, 'succeeded'
        )

    def test_change_start_back_again(self):
        self.test_change_start_with_contributions()

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = now() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

        self.assertEqual(
            self.rejected.contribution_values.get().status, 'failed'
        )

        self.assertEqual(
            self.accepted.contribution_values.get().status, 'new'
        )

    def test_change_start_full(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.application_factory.create_batch(
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


class PeriodActivityTriggerTestCase(TimeBasedActivityTriggerTestCase, BluebottleTestCase):
    factory = PeriodActivityFactory
    application_factory = PeriodApplicationFactory

    def test_change_deadline(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'cancelled')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.deadline = date.today() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def test_change_deadline_with_contributions(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.application_factory.create(
            activity=self.activity,
            status='accepted'
        )
        self.assertEqual(self.activity.status, 'open')

        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'succeeded')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.deadline = date.today() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def test_change_deadline_full(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.application_factory.create_batch(
            self.activity.capacity,
            activity=self.activity,
        )

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')

        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'succeeded')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.deadline = date.today() + timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

    def test_change_start(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.activity.start = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'running')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = date.today() + timedelta(days=2)
        self.activity.save()

        self.assertEqual(self.activity.status, 'open')

    def test_change_start_after_registration_deadline(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.activity.registration_deadline = date.today() - timedelta(days=4)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)
        self.activity.start = date.today() - timedelta(days=1)

        self.activity.save()

        self.assertEqual(self.activity.status, 'running')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = date.today() + timedelta(days=2)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')

    def test_change_start_after_full(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.application_factory.create_batch(
            self.activity.capacity,
            activity=self.activity,
        )

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'full')

        self.activity.start = date.today() - timedelta(days=1)

        self.activity.save()

        self.assertEqual(self.activity.status, 'running')

        self.activity = self.factory._meta.model.objects.get(pk=self.activity.pk)

        self.activity.start = date.today() + timedelta(days=2)
        self.activity.save()

        self.assertEqual(self.activity.status, 'full')


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
        application = self.application_factory.create(activity=self.review_activity)

        self.assertEqual(application.status, 'new')

    def test_initial_no_review(self):
        application = self.application_factory.create(activity=self.activity)

        self.assertEqual(application.status, 'accepted')

    def test_no_review_fill(self):
        self.application_factory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')

    def test_review_fill(self):
        applications = self.application_factory.create_batch(
            self.review_activity.capacity, activity=self.review_activity
        )
        self.review_activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        for application in applications:
            application.states.accept(save=True)

        self.review_activity.refresh_from_db()

        self.assertEqual(self.review_activity.status, 'full')

    def test_reject(self):
        self.applications = self.application_factory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')
        self.applications[0].states.reject(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'open')

    def test_reaccept(self):
        self.test_reject()

        self.applications[0].states.accept(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'full')

    def test_withdraw(self):
        self.applications = self.application_factory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')

        self.applications[0].states.withdraw(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'open')

    def test_reapply(self):
        self.test_withdraw()

        self.applications[0].states.reapply(save=True)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')


class DateApplicationTriggerTestCase(ApplicationTriggerTestCase, BluebottleTestCase):
    factory = DateActivityFactory
    application_factory = OnADateApplicationFactory

    def test_no_review_succeed_after_cancel(self):
        self.activity.start = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'cancelled')

        self.application_factory.create(activity=self.activity)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')

    def test_initial_no_review(self):
        super().test_initial_no_review()

        self.assertEqual(
            self.activity.accepted_applications.get().contribution_values.get().status,
            'new'
        )

    def test_initial_review(self):
        super().test_initial_review()

        self.assertEqual(
            self.review_activity.applications.get().contribution_values.get().status,
            'new'
        )

    def test_withdraw(self):
        super().test_withdraw()

        self.assertEqual(
            self.applications[0].contribution_values.get().status,
            'failed'
        )

    def test_reapply(self):
        super().test_reapply()

        self.assertEqual(
            self.applications[0].contribution_values.get().status,
            'new'
        )

    def test_reject(self):
        super().test_reject()

        self.assertEqual(
            self.applications[0].contribution_values.get().status,
            'failed'
        )

    def test_reaccept(self):
        super().test_reaccept()

        self.assertEqual(
            self.applications[0].contribution_values.get().status,
            'new'
        )


class PeriodApplicationTriggerTestCase(ApplicationTriggerTestCase, BluebottleTestCase):
    factory = PeriodActivityFactory
    application_factory = PeriodApplicationFactory

    def test_no_review_succeed(self):
        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'cancelled')

        self.application_factory.create(activity=self.activity)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')
