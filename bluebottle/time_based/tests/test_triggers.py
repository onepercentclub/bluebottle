from datetime import timedelta, date

from django.utils.timezone import now

from bluebottle.time_based.tests.factories import (
    DateActivityFactory, PeriodActivityFactory,
    DateParticipantFactory, PeriodParticipantFactory
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
        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, 'new')

    def test_delete(self):
        self.activity.states.delete(save=True)
        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, 'failed')

    def test_reject(self):
        self.initiative.states.submit(save=True)
        self.activity.states.submit()
        self.activity.states.reject(save=True)
        organizer = self.activity.contributors.instance_of(Organizer).get()
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

        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(organizer.status, 'succeeded')

    def test_change_capacity(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create_batch(
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
    participant_factory = DateParticipantFactory

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

    def test_change_start_with_contributors(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.accepted = self.participant_factory.create(
            activity=self.activity,
        )

        self.rejected = self.participant_factory.create(
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
        self.test_change_start_with_contributors()

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

        self.participant_factory.create_batch(
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
    participant_factory = PeriodParticipantFactory

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

    def test_change_deadline_with_contributors(self):
        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)

        self.activity.refresh_from_db()

        self.participant_factory.create(
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

        self.participant_factory.create_batch(
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

        self.participant_factory.create_batch(
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


class ParticipantTriggerTestCase():

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
        participant = self.participant_factory.create(activity=self.review_activity)

        self.assertEqual(participant.status, 'new')

    def test_initial_no_review(self):
        participant = self.participant_factory.create(activity=self.activity)

        self.assertEqual(participant.status, 'accepted')

    def test_no_review_fill(self):
        self.participant_factory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')

    def test_review_fill(self):
        participants = self.participant_factory.create_batch(
            self.review_activity.capacity, activity=self.review_activity
        )
        self.review_activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'open')

        for participant in participants:
            participant.states.accept(save=True)

        self.review_activity.refresh_from_db()

        self.assertEqual(self.review_activity.status, 'full')

    def test_reject(self):
        self.participants = self.participant_factory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')
        self.participants[0].states.reject(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'open')

    def test_reaccept(self):
        self.test_reject()

        self.participants[0].states.accept(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'full')

    def test_withdraw(self):
        self.participants = self.participant_factory.create_batch(
            self.activity.capacity, activity=self.activity
        )
        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')

        self.participants[0].states.withdraw(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, 'open')

    def test_reapply(self):
        self.test_withdraw()

        self.participants[0].states.reapply(save=True)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'full')


class DateParticipantTriggerTestCase(ParticipantTriggerTestCase, BluebottleTestCase):
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory

    def test_no_review_succeed_after_cancel(self):
        self.activity.start = now() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'cancelled')

        self.participant_factory.create(activity=self.activity)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')

    def test_initial_no_review(self):
        super().test_initial_no_review()

        self.assertEqual(
            self.activity.accepted_participants.get().contribution_values.get().status,
            'new'
        )

    def test_initial_review(self):
        super().test_initial_review()

        self.assertEqual(
            self.review_activity.participants.get().contribution_values.get().status,
            'new'
        )

    def test_withdraw(self):
        super().test_withdraw()

        self.assertEqual(
            self.participants[0].contribution_values.get().status,
            'failed'
        )

    def test_reapply(self):
        super().test_reapply()

        self.assertEqual(
            self.participants[0].contribution_values.get().status,
            'new'
        )

    def test_reject(self):
        super().test_reject()

        self.assertEqual(
            self.participants[0].contribution_values.get().status,
            'failed'
        )

    def test_reaccept(self):
        super().test_reaccept()

        self.assertEqual(
            self.participants[0].contribution_values.get().status,
            'new'
        )


class PeriodParticipantTriggerTestCase(ParticipantTriggerTestCase, BluebottleTestCase):
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

    def test_no_review_succeed(self):
        self.activity.deadline = date.today() - timedelta(days=1)
        self.activity.save()

        self.assertEqual(self.activity.status, 'cancelled')

        self.participant_factory.create(activity=self.activity)

        self.activity.refresh_from_db()

        self.assertEqual(self.activity.status, 'succeeded')
