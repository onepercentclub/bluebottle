from bluebottle.activities.effects import (
    CreateOrganizer, CreateOrganizerContribution, SetContributionDateEffect,
    TeamContributionTransitionEffect, ResetTeamParticipantsEffect, CreateInviteForOwnerEffect
)
from bluebottle.activities.messages import (
    TeamAddedMessage, TeamReopenedMessage, TeamAppliedMessage,
    TeamWithdrawnMessage, TeamWithdrawnActivityOwnerMessage, TeamReappliedMessage, TeamCancelledMessage
)
from bluebottle.activities.models import Organizer, EffortContribution, Team
from bluebottle.activities.states import (
    ActivityStateMachine, OrganizerStateMachine, ContributionStateMachine,
    EffortContributionStateMachine, TeamStateMachine
)
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    TriggerManager, TransitionTrigger, ModelDeletedTrigger, register, ModelChangedTrigger
)
from bluebottle.impact.effects import UpdateImpactGoalEffect
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.messages import TeamParticipantJoinedNotification
from bluebottle.time_based.states import ParticipantStateMachine, TimeBasedStateMachine, TeamSlotStateMachine


def initiative_is_approved(effect):
    """
    The initiative is approved
    """
    return effect.instance.initiative.status == 'approved'


def has_organizer(effect):
    """
    Has an organizer
    """
    return getattr(effect.instance, 'organizer', False)


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
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.fail,
                    conditions=[has_organizer]
                )
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.auto_approve,
            effects=[
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.succeed,
                    conditions=[has_organizer]
                ),
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.fail,
                    conditions=[has_organizer]
                )
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.expire,
            effects=[
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.fail,
                    conditions=[has_organizer]),
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.restore,
            effects=[
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.reset,
                    conditions=[has_organizer]
                )
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.delete,
            effects=[
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.fail,
                    conditions=[has_organizer]
                )
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


def automatically_accept_team(effect):
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


def team_activity_will_be_full(effect):
    """
    the activity is full
    """
    activity = effect.instance.activity
    accepted_teams = activity.teams.filter(status__in=['open', 'running', 'finished']).count() + 1
    return not hasattr(activity, 'capacity') or (
        activity.capacity and
        activity.capacity <= accepted_teams
    )


def team_activity_will_not_be_full(effect):
    """
    the activity is full
    """
    activity = effect.instance.activity
    accepted_teams = activity.teams.filter(status__in=['open', 'running', 'finished']).count() - 1

    return (
        not getattr(activity, 'capacity', False) or
        activity.capacity > accepted_teams
    )


@register(Team)
class TeamTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            TeamStateMachine.initiate,
            effects=[
                NotificationEffect(
                    TeamAddedMessage,
                    conditions=[automatically_accept_team]
                ),
                NotificationEffect(
                    TeamAppliedMessage,
                    conditions=[
                        needs_review,
                    ]
                ),
                TransitionEffect(
                    TeamStateMachine.accept,
                    conditions=[
                        automatically_accept_team
                    ]
                ),
            ]
        ),

        TransitionTrigger(
            TeamStateMachine.accept,
            effects=[
                NotificationEffect(
                    TeamParticipantJoinedNotification,
                    conditions=[
                        automatically_accept_team
                    ]
                ),
                RelatedTransitionEffect(
                    'members',
                    ParticipantStateMachine.accept,
                    conditions=[
                        needs_review
                    ]
                ),
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.lock,
                    conditions=[team_activity_will_be_full]
                ),
            ]
        ),

        TransitionTrigger(
            TeamStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.reopen,
                    conditions=[team_activity_will_not_be_full]
                ),
                TeamContributionTransitionEffect(ContributionStateMachine.fail),
                NotificationEffect(TeamCancelledMessage),
                RelatedTransitionEffect(
                    'slot',
                    TeamSlotStateMachine.cancel,
                ),
            ]
        ),

        TransitionTrigger(
            TeamStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.reopen,
                    conditions=[team_activity_will_not_be_full]
                ),
                TeamContributionTransitionEffect(ContributionStateMachine.fail),
                NotificationEffect(TeamWithdrawnMessage),
                NotificationEffect(TeamWithdrawnActivityOwnerMessage),
                RelatedTransitionEffect(
                    'slot',
                    TeamSlotStateMachine.cancel,
                ),
            ]
        ),

        TransitionTrigger(
            TeamStateMachine.reopen,
            effects=[
                NotificationEffect(TeamReopenedMessage),
                TeamContributionTransitionEffect(
                    ContributionStateMachine.reset,
                    contribution_conditions=[
                        activity_is_active,
                        contributor_is_active
                    ]
                ),
                RelatedTransitionEffect(
                    'slot',
                    TeamSlotStateMachine.reopen
                ),

            ]
        ),

        TransitionTrigger(
            TeamStateMachine.reapply,
            effects=[
                TeamContributionTransitionEffect(
                    ContributionStateMachine.reset,
                    contribution_conditions=[
                        activity_is_active,
                        contributor_is_active
                    ]
                ),
                NotificationEffect(TeamReappliedMessage),
                NotificationEffect(TeamAddedMessage),
                RelatedTransitionEffect(
                    'slot',
                    TeamSlotStateMachine.reopen,
                ),
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
                NotificationEffect(TeamAddedMessage),
                RelatedTransitionEffect(
                    'slot',
                    TeamSlotStateMachine.reopen,
                ),

            ]
        ),

        TransitionTrigger(
            TeamStateMachine.finish,
            effects=[
                TeamContributionTransitionEffect(
                    ContributionStateMachine.succeed,
                    contribution_conditions=[
                        contributor_is_active
                    ]
                ),
            ]
        ),
        ModelChangedTrigger(
            'owner',
            effects=[
                CreateInviteForOwnerEffect,
            ]
        ),

    ]
