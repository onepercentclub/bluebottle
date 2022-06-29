from bluebottle.activities.models import Organizer, EffortContribution, Team
from bluebottle.fsm.triggers import (
    TriggerManager, TransitionTrigger, ModelDeletedTrigger, register
)
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.notifications.effects import NotificationEffect

from bluebottle.activities.states import (
    ActivityStateMachine, OrganizerStateMachine, ContributionStateMachine,
    EffortContributionStateMachine, TeamStateMachine
)
from bluebottle.activities.effects import (
    CreateOrganizer, CreateOrganizerContribution, SetContributionDateEffect,
    TeamContributionTransitionEffect, ResetTeamParticipantsEffect
)

from bluebottle.activities.messages import (
    TeamAddedMessage, TeamCancelledMessage, TeamReopenedMessage, TeamAcceptedMessage, TeamAppliedMessage,
    TeamWithdrawnMessage, TeamWithdrawnActivityOwnerMessage, TeamCancelledTeamCaptainMessage,
    TeamReappliedMessage
)

from bluebottle.time_based.states import ParticipantStateMachine
from bluebottle.impact.effects import UpdateImpactGoalEffect


def initiative_is_approved(effect):
    """
    The initiative is approved
    """
    return effect.instance.initiative.status == 'approved'


class ActivityTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            ActivityStateMachine.initiate,
            effects=[
                CreateOrganizer
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.submit,
            effects=[
                TransitionEffect(
                    ActivityStateMachine.auto_approve,
                    conditions=[initiative_is_approved]
                )
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.auto_submit,
            effects=[
                TransitionEffect(
                    ActivityStateMachine.auto_approve,
                    conditions=[initiative_is_approved]
                )
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.reject,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail)
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.auto_approve,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.succeed),
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail)
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.expire,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.restore,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.reset)
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.delete,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail)
            ]
        ),
    ]


class ContributorTriggers(TriggerManager):
    triggers = []


class ContributionTriggers(TriggerManager):
    triggers = []


@register(Organizer)
class OrganizerTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            OrganizerStateMachine.initiate,
            effects=[
                CreateOrganizerContribution
            ]
        ),
        TransitionTrigger(
            OrganizerStateMachine.fail,
            effects=[
                RelatedTransitionEffect(
                    'contributions', EffortContributionStateMachine.fail, display=False
                )
            ]
        ),
        TransitionTrigger(
            OrganizerStateMachine.reset,
            effects=[
                RelatedTransitionEffect(
                    'contributions', EffortContributionStateMachine.reset, display=False
                )
            ]
        ),
        TransitionTrigger(
            OrganizerStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'contributions', EffortContributionStateMachine.succeed, display=False
                )
            ]
        ),
    ]


def contributor_is_succeeded(effect):
    return effect.instance.contributor.status == 'succeeded'


@register(EffortContribution)
class EffortContributionTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            EffortContributionStateMachine.initiate,
            effects=[
                UpdateImpactGoalEffect,
                TransitionEffect(
                    EffortContributionStateMachine.succeed,
                    conditions=[contributor_is_succeeded]
                )
            ]
        ),
        TransitionTrigger(
            EffortContributionStateMachine.succeed,
            effects=[
                SetContributionDateEffect,
                UpdateImpactGoalEffect
            ]
        ),

        TransitionTrigger(
            EffortContributionStateMachine.reset,
            effects=[
                UpdateImpactGoalEffect
            ]
        ),

        TransitionTrigger(
            EffortContributionStateMachine.fail,
            effects=[
                UpdateImpactGoalEffect
            ]
        ),

        ModelDeletedTrigger(
            effects=[
                UpdateImpactGoalEffect
            ]
        ),
    ]


def activity_is_active(contribution):
    """activity is not cancelled, expired or rejected"""
    return contribution.contributor.activity.status not in [
        ActivityStateMachine.cancelled.value,
        ActivityStateMachine.expired.value,
        ActivityStateMachine.rejected.value
    ]


def contributor_is_active(contribution):
    """contributor is accepted"""
    return contribution.contributor.status in [
        ParticipantStateMachine.accepted.value
    ]


def automatically_accept(effect):
    """
    automatically accept team
    """
    captain = effect.instance.activity\
        .contributors.not_instance_of(Organizer)\
        .filter(user=effect.instance.owner).first()
    return (
        not hasattr(effect.instance.activity, 'review') or
        not effect.instance.activity.review or
        (captain and captain.status == 'accepted')
    )


def needs_review(effect):
    """
    needs review
    """
    return hasattr(effect.instance.activity, 'review') and effect.instance.activity.review


@register(Team)
class TeamTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            TeamStateMachine.initiate,
            effects=[
                NotificationEffect(
                    TeamAddedMessage,
                    conditions=[automatically_accept]
                ),
                NotificationEffect(
                    TeamAppliedMessage,
                    conditions=[needs_review]
                ),
                TransitionEffect(
                    TeamStateMachine.accept,
                    conditions=[
                        automatically_accept
                    ]
                )
            ]
        ),

        TransitionTrigger(
            TeamStateMachine.accept,
            effects=[
                NotificationEffect(
                    TeamAcceptedMessage,
                    conditions=[needs_review]
                ),
                RelatedTransitionEffect(
                    'members',
                    ParticipantStateMachine.accept,
                    conditions=[needs_review]
                )
            ]
        ),

        TransitionTrigger(
            TeamStateMachine.cancel,
            effects=[
                TeamContributionTransitionEffect(ContributionStateMachine.fail),
                NotificationEffect(TeamCancelledMessage),
                NotificationEffect(TeamCancelledTeamCaptainMessage)
            ]
        ),

        TransitionTrigger(
            TeamStateMachine.withdraw,
            effects=[
                TeamContributionTransitionEffect(ContributionStateMachine.fail),
                NotificationEffect(TeamWithdrawnMessage),
                NotificationEffect(TeamWithdrawnActivityOwnerMessage)
            ]
        ),

        TransitionTrigger(
            TeamStateMachine.reopen,
            effects=[
                NotificationEffect(TeamReopenedMessage),
                TeamContributionTransitionEffect(
                    ContributionStateMachine.reset,
                    contribution_conditions=[activity_is_active, contributor_is_active]
                ),

            ]
        ),

        TransitionTrigger(
            TeamStateMachine.reapply,
            effects=[
                TeamContributionTransitionEffect(
                    ContributionStateMachine.reset,
                    contribution_conditions=[activity_is_active, contributor_is_active]
                ),
                NotificationEffect(TeamReappliedMessage)
            ]
        ),

        TransitionTrigger(
            TeamStateMachine.reset,
            effects=[
                TeamContributionTransitionEffect(
                    ContributionStateMachine.reset,
                    contribution_conditions=[activity_is_active, contributor_is_active]
                ),
                ResetTeamParticipantsEffect,
                NotificationEffect(TeamAddedMessage)
            ]
        ),
    ]
