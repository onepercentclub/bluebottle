from datetime import timedelta

from django.core import mail
from django.utils.timezone import now

from bluebottle.activities.messages.activity_manager import ActivityCancelledNotification
from bluebottle.deeds.tests.factories import DeedFactory

from bluebottle.deeds.states import DeedStateMachine
from bluebottle.funding.states import FundingStateMachine
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.funding_stripe.tests.factories import (
    ExternalAccountFactory,
    StripePayoutAccountFactory,
)
from bluebottle.initiatives.messages.initiator import InitiativeSubmittedInitiatorMessage, \
    InitiativePublishedInitiatorMessage, InitiativeRejectedInitiatorMessage, InitiativeApprovedInitiatorMessage, \
    InitiativeCancelledInitiatorMessage
from bluebottle.initiatives.messages.reviewer import InitiativeSubmittedReviewerMessage, \
    InitiativePublishedReviewerMessage
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, TriggerTestCase
from bluebottle.time_based.messages import SlotCancelledNotification
from bluebottle.time_based.models import TimeContribution
from bluebottle.time_based.states import (
    DateStateMachine,
    DateActivitySlotStateMachine,
    DateParticipantStateMachine,
    TimeContributionStateMachine
)
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DateParticipantFactory,
)
from bluebottle.activities.states import ActivityStateMachine


class InitiativeOldTriggerTests(BluebottleTestCase):

    def setUp(self):
        super(InitiativeOldTriggerTests, self).setUp()
        self.user = BlueBottleUserFactory.create(first_name='Bart', last_name='Lacroix')
        self.initiative = InitiativeFactory.create(
            has_organization=False,
            owner=self.user,
            organization=None
        )

    def test_set_reviewer(self):
        mail.outbox = []
        self.initiative.reviewer = BlueBottleUserFactory.create(email='reviewer@goodup.com')
        self.initiative.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('You are assigned as reviewer' in mail.outbox[0].body)
        self.assertEqual(['reviewer@goodup.com'], mail.outbox[0].to)


class InitiativeTriggerTestCase(TriggerTestCase):
    factory = InitiativeFactory

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(
            is_staff=True,
            submitted_initiative_notifications=True
        )
        self.defaults = {
            'owner': self.owner,
        }
        super().setUp()

    def test_submit(self):
        self.create()
        self.model.states.submit()
        with self.execute():
            self.assertNotificationEffect(InitiativeSubmittedReviewerMessage)
            self.assertNotificationEffect(InitiativeSubmittedInitiatorMessage)
        self.model.save()
        self.assertEqual(self.model.published, None)
        self.assertStatus(self.model, 'submitted')

    def test_publish(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_reviewing = False
        initiative_settings.save()
        self.create()
        self.model.states.publish()
        with self.execute():
            self.assertNotificationEffect(InitiativePublishedInitiatorMessage)
            self.assertNotificationEffect(InitiativePublishedReviewerMessage)
        self.model.save()
        self.assertStatus(self.model, 'approved')

    def test_reject(self):
        self.create()
        self.model.states.submit(save=True)
        self.model.states.reject()
        with self.execute():
            self.assertNotificationEffect(InitiativeRejectedInitiatorMessage)

    def test_approve(self):
        self.create()
        self.model.states.submit(save=True)
        self.model.states.approve()
        with self.execute():
            self.assertNotificationEffect(InitiativeApprovedInitiatorMessage)

    def test_auto_submit_activity(self):
        self.create()
        activity = DeedFactory.create(initiative=self.model)

        self.model.states.submit()
        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.auto_submit, activity)

    def test_auto_submit_funding_activity(self):
        self.create()
        activity = FundingFactory.create(initiative=self.model)

        self.model.states.submit()
        with self.execute():
            self.assertNoTransitionEffect(FundingStateMachine.auto_submit, activity)

    def test_auto_submit_funding_activity_complete(self):
        self.create()
        activity = FundingFactory.create(
            initiative=self.model,
            bank_account=ExternalAccountFactory.create(
                status="verified",
                connect_account=StripePayoutAccountFactory.create(
                    status="verified", account_id='test-account-id'
                ),
            ),
        )

        self.model.states.submit()
        with self.execute():
            self.assertNoTransitionEffect(FundingStateMachine.auto_submit, activity)

    def test_cancel_initiative_cancels_date_activity(self):
        """Test that cancelling an Initiative auto-cancels all DateActivities"""
        self.create()
        self.model.states.submit(save=True)
        self.model.states.approve(save=True)

        # Create a DateActivity with slots
        date_activity = DateActivityFactory.create(
            initiative=self.model,
            status='open',
            registration_deadline=None,
            review=False,
            slots=[]
        )
        DateActivitySlotFactory.create(
            activity=date_activity,
            start=now() + timedelta(days=2),
            status='open'
        )
        DateActivitySlotFactory.create(
            activity=date_activity,
            start=now() + timedelta(days=3),
            status='open'
        )

        self.model.states.cancel()
        with self.execute(user=self.staff_user):
            self.assertTransitionEffect(ActivityStateMachine.auto_cancel, date_activity)
            self.assertNotificationEffect(InitiativeCancelledInitiatorMessage)

        self.model.save()
        self.assertStatus(self.model, 'cancelled')
        self.assertStatus(date_activity, 'cancelled')

    def test_cancel_initiative_cancels_date_activity_slots(self):
        """Test that cancelling an Initiative cancels DateActivitySlots"""
        self.create()
        self.model.states.submit(save=True)
        self.model.states.approve(save=True)

        # Create a DateActivity with slots
        date_activity = DateActivityFactory.create(
            initiative=self.model,
            status='open',
            registration_deadline=None,
            review=False,
            slots=[]
        )
        slot1 = DateActivitySlotFactory.create(
            activity=date_activity,
            start=now() + timedelta(days=2),
            status='open'
        )
        slot2 = DateActivitySlotFactory.create(
            activity=date_activity,
            start=now() + timedelta(days=3),
            status='full'
        )

        self.model.states.cancel()
        with self.execute():
            self.assertTransitionEffect(ActivityStateMachine.auto_cancel, date_activity)
            self.assertTransitionEffect(DateActivitySlotStateMachine.auto_cancel, slot1)
            self.assertTransitionEffect(DateActivitySlotStateMachine.auto_cancel, slot2)

        self.model.save()
        self.assertStatus(date_activity, 'cancelled')
        self.assertStatus(slot1, 'cancelled')
        self.assertStatus(slot2, 'cancelled')

    def test_cancel_initiative_fails_time_contributions(self):
        """Test that cancelling an Initiative fails all TimeContributions"""
        self.create()
        self.model.states.submit(save=True)
        self.model.states.approve(save=True)

        # Create a DateActivity with slots and participants
        date_activity = DateActivityFactory.create(
            initiative=self.model,
            status='open',
            registration_deadline=None,
            review=False,
            slots=[]
        )
        slot1 = DateActivitySlotFactory.create(
            activity=date_activity,
            start=now() + timedelta(days=2),
            status='open'
        )

        participant1 = DateParticipantFactory.create(
            activity=date_activity,
            slot=slot1,
            status='accepted'
        )
        participant2 = DateParticipantFactory.create(
            activity=date_activity,
            slot=slot1,
            status='accepted'
        )

        contribution1 = TimeContribution.objects.create(
            contributor=participant1,
            value=timedelta(hours=2),
            status='succeeded',
            start=now() + timedelta(days=1)
        )
        contribution2 = TimeContribution.objects.create(
            contributor=participant2,
            value=timedelta(hours=3),
            status='succeeded',
            start=now() + timedelta(days=1)
        )
        contribution3 = TimeContribution.objects.create(
            contributor=participant1,
            value=timedelta(hours=1),
            status='new',
            start=now() + timedelta(days=1)
        )

        self.model.states.cancel()
        with self.execute():
            self.assertTransitionEffect(ActivityStateMachine.auto_cancel, date_activity)

        self.model.save()

        self.assertStatus(date_activity, 'cancelled')
        self.assertStatus(participant1, 'cancelled')
        self.assertStatus(participant2, 'cancelled')
        self.assertStatus(contribution1, 'failed')
        self.assertStatus(contribution2, 'failed')
        self.assertStatus(contribution3, 'failed')

    def test_cancel_initiative_with_multiple_activities(self):
        """Test that cancelling an Initiative cancels all activities including DateActivity"""
        self.create()
        self.model.states.submit(save=True)
        self.model.states.approve(save=True)

        # Create multiple activities
        deed = DeedFactory.create(initiative=self.model, status='open')
        date_activity = DateActivityFactory.create(
            initiative=self.model,
            status='open',
            registration_deadline=None,
            review=False,
            slots=[]
        )
        slot = DateActivitySlotFactory.create(
            activity=date_activity,
            start=now() + timedelta(days=2),
            status='open'
        )

        participant = DateParticipantFactory.create(
            activity=date_activity,
            slot=slot,
            status='accepted'
        )

        contribution = TimeContribution.objects.create(
            contributor=participant,
            value=timedelta(hours=2),
            status='succeeded',
            start=now() + timedelta(days=1)
        )

        # Cancel the initiative
        self.model.states.cancel()
        with self.execute():
            # Verify both activities are auto-cancelled
            self.assertTransitionEffect(ActivityStateMachine.auto_cancel, deed)
            self.assertTransitionEffect(ActivityStateMachine.auto_cancel, date_activity)
            self.assertNotificationEffect(InitiativeCancelledInitiatorMessage)

        # Save and verify all are cancelled
        self.model.save()
        deed.refresh_from_db()
        date_activity.refresh_from_db()
        participant.refresh_from_db()
        contribution.refresh_from_db()

        self.assertStatus(deed, 'cancelled')
        self.assertStatus(date_activity, 'cancelled')
        self.assertStatus(participant, 'cancelled')
        self.assertStatus(contribution, 'failed')
