from django.core import mail

from bluebottle.test.utils import TriggerTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.activities.messages import (
    TeamAddedMessage, TeamCancelledMessage, TeamReopenedMessage,
    TeamAppliedMessage, TeamAcceptedMessage, TeamCancelledTeamCaptainMessage, TeamWithdrawnMessage,
    TeamWithdrawnActivityOwnerMessage, TeamReappliedMessage
)
from bluebottle.activities.effects import TeamContributionTransitionEffect, ResetTeamParticipantsEffect
from bluebottle.time_based.models import PeriodParticipant
from bluebottle.activities.tests.factories import TeamFactory

from bluebottle.time_based.tests.factories import PeriodActivityFactory, PeriodParticipantFactory
from bluebottle.time_based.states import TimeContributionStateMachine


class TeamTriggersTestCase(TriggerTestCase):
    factory = TeamFactory

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.activity = PeriodActivityFactory.create()
        self.activity.initiative.states.submit(save=True)
        self.activity.initiative.states.approve(save=True)
        self.activity.refresh_from_db()

        self.staff_user = BlueBottleUserFactory.create(is_staff=True)

        self.defaults = {
            'activity': self.activity,
            'owner': self.owner
        }
        super().setUp()

    def create(self):
        super().create()

        self.participant = PeriodParticipantFactory.create(
            activity=self.activity,
            user=self.model.owner,
            team=self.model
        )

    def test_initiate(self):
        self.model = self.factory.build(**self.defaults)

        with self.execute():
            self.assertEqual(self.model.status, 'open')
            self.assertNotificationEffect(TeamAddedMessage)

    def test_apply(self):
        self.activity.review = True
        self.activity.save()
        self.model = self.factory.build(**self.defaults)

        with self.execute():
            self.assertEqual(self.model.status, 'new')
            self.assertNotificationEffect(TeamAppliedMessage)

    def test_accept(self):
        self.activity.review = True
        self.activity.save()
        self.model = self.factory.build(**self.defaults)
        self.model.save()
        self.model.states.accept()

        message = 'You were accepted, because you were great'

        with self.execute(message=message):
            self.assertEqual(self.model.status, 'open')

            self.assertNotificationEffect(TeamAcceptedMessage)
            self.assertEqual(
                self.effects[0].options['message'], message
            )

        self.model.save()
        self.assertTrue(message in mail.outbox[-1].body)

    def test_cancel(self):
        self.create()

        other_participant = PeriodParticipantFactory.create(
            activity=self.activity,
            team=self.model
        )
        self.model.states.cancel()

        with self.execute():
            self.assertEffect(TeamContributionTransitionEffect(TimeContributionStateMachine.fail))
            self.assertNotificationEffect(
                TeamCancelledMessage, [other_participant.user]
            )
            self.assertNotificationEffect(
                TeamCancelledTeamCaptainMessage, [self.model.owner]
            )

        self.model.save()
        self.participant.refresh_from_db()

        for contribution in self.participant.contributions.all():
            self.assertEqual(contribution.status, TimeContributionStateMachine.failed.value)

    def test_withdrawn(self):
        self.create()

        self.model.states.withdraw()

        with self.execute():
            self.assertEffect(TeamContributionTransitionEffect(TimeContributionStateMachine.fail))
            self.assertNotificationEffect(
                TeamWithdrawnMessage, [member.user for member in self.model.members.all()]
            )
            self.assertNotificationEffect(
                TeamWithdrawnActivityOwnerMessage, [self.model.activity.owner]
            )

        self.model.save()
        self.participant.refresh_from_db()

        for contribution in self.participant.contributions.all():
            self.assertEqual(contribution.status, TimeContributionStateMachine.failed.value)

    def test_reapply(self):
        self.create()

        PeriodParticipantFactory.create(
            activity=self.activity,
            team=self.model
        )

        for contribution in self.participant.contributions.all():
            self.assertEqual(contribution.status, TimeContributionStateMachine.new.value)

        self.model.states.withdraw(save=True)

        self.model.states.reapply()

        with self.execute():
            self.assertEffect(TeamContributionTransitionEffect(TimeContributionStateMachine.reset))
            self.assertNotificationEffect(
                TeamReappliedMessage,
                [member.user for member in self.model.members.all() if member.user != self.model.owner]
            )

            self.assertNotificationEffect(
                TeamAddedMessage,
                [self.model.activity.owner]
            )

        self.model.save()
        self.participant.refresh_from_db()

        for contribution in self.participant.contributions.all():
            self.assertEqual(contribution.status, TimeContributionStateMachine.new.value)

    def test_reset(self):
        self.create()
        other_participant = PeriodParticipantFactory.create(
            team=self.model, activity=self.activity
        )

        self.model.states.withdraw(save=True)

        self.model.states.reset()

        with self.execute():
            self.assertEffect(TeamContributionTransitionEffect(TimeContributionStateMachine.reset))
            self.assertEffect(ResetTeamParticipantsEffect)
            self.assertNotificationEffect(
                TeamAddedMessage,
                [self.activity.owner]
            )

        self.model.save()

        with self.assertRaises(PeriodParticipant.DoesNotExist):
            other_participant.refresh_from_db()

        for contribution in self.participant.contributions.all():
            self.assertEqual(contribution.status, TimeContributionStateMachine.new.value)

    def test_reopen(self):
        self.create()

        self.model.states.cancel(save=True)
        self.model.states.reopen()

        with self.execute():
            self.assertNotificationEffect(TeamReopenedMessage)
            self.assertEffect(TeamContributionTransitionEffect(TimeContributionStateMachine.reset))

    def test_reopen_withdrawn(self):
        self.create()

        self.participant.states.withdraw(save=True)
        self.model.states.cancel(save=True)
        self.model.states.reopen()

        with self.execute():
            self.assertNoEffect(TeamContributionTransitionEffect(TimeContributionStateMachine.succeed))

    def test_reopen_cancelled_activity(self):
        self.create()

        self.activity.states.cancel(save=True)
        self.model.states.cancel(save=True)
        self.model.states.reopen()

        with self.execute():
            self.assertNoEffect(TeamContributionTransitionEffect(TimeContributionStateMachine.reset))
