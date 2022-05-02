from datetime import date

from bluebottle.activities.messages import (
    ActivityExpiredNotification, ActivitySucceededNotification,
    ActivityRejectedNotification, ActivityCancelledNotification,
    ActivityRestoredNotification, ParticipantWithdrewConfirmationNotification,
    TeamMemberAddedMessage, TeamMemberWithdrewMessage, TeamMemberRemovedMessage
)
from bluebottle.time_based.messages import (
    ParticipantWithdrewNotification, ParticipantRemovedNotification, ParticipantRemovedOwnerNotification,
    TeamParticipantRemovedNotification, NewParticipantNotification, ParticipantAddedOwnerNotification,
    ParticipantAddedNotification
)
from bluebottle.activities.states import OrganizerStateMachine, TeamStateMachine
from bluebottle.activities.triggers import (
    ActivityTriggers, ContributorTriggers, ContributionTriggers, TeamTriggers
)
from bluebottle.activities.effects import CreateTeamEffect, CreateInviteEffect

from bluebottle.collect.effects import CreateCollectContribution, SetOverallContributor
from bluebottle.collect.messages import (
    CollectActivityDateChangedNotification, ParticipantJoinedNotification
)
from bluebottle.collect.models import CollectActivity, CollectContributor, CollectContribution
from bluebottle.collect.states import (
    CollectActivityStateMachine, CollectContributorStateMachine, CollectContributionStateMachine,
)
from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import (
    register, TransitionTrigger, ModelChangedTrigger
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.impact.effects import UpdateImpactGoalsForActivityEffect


def is_finished(effect):
    """
    has finished
    """
    return (
        effect.instance.end and
        effect.instance.end < date.today()
    )


def is_not_finished(effect):
    """
    hasn't finished yet
    """
    return not is_finished(effect)


def has_contributors(effect):
    """ has contributors"""
    return len(effect.instance.active_contributors) > 0


def has_no_contributors(effect):
    """ has no contributors"""
    return not has_contributors(effect)


def has_start_date(effect):
    """has start date"""
    return effect.instance.start


@register(CollectActivity)
class CollectActivityTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [
        ModelChangedTrigger(
            'end',
            effects=[
                TransitionEffect(
                    CollectActivityStateMachine.reopen, conditions=[is_not_finished]
                ),
                TransitionEffect(
                    CollectActivityStateMachine.succeed, conditions=[is_finished, has_contributors]
                ),
                TransitionEffect(
                    CollectActivityStateMachine.expire, conditions=[is_finished, has_no_contributors]
                ),
                NotificationEffect(
                    CollectActivityDateChangedNotification,
                    conditions=[
                        is_not_finished
                    ]
                )
            ]
        ),

        ModelChangedTrigger(
            'enable_impact',
            effects=[UpdateImpactGoalsForActivityEffect]
        ),

        ModelChangedTrigger(
            'target',
            effects=[UpdateImpactGoalsForActivityEffect]
        ),

        ModelChangedTrigger(
            'realized',
            effects=[UpdateImpactGoalsForActivityEffect]
        ),

        TransitionTrigger(
            CollectActivityStateMachine.auto_approve,
            effects=[
                TransitionEffect(CollectActivityStateMachine.reopen, conditions=[is_not_finished]),
                TransitionEffect(
                    CollectActivityStateMachine.succeed, conditions=[is_finished, has_contributors]
                ),
                TransitionEffect(
                    CollectActivityStateMachine.expire, conditions=[is_finished, has_no_contributors]
                ),
            ]
        ),

        TransitionTrigger(
            CollectActivityStateMachine.expire,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(ActivityExpiredNotification)
            ]
        ),

        TransitionTrigger(
            CollectActivityStateMachine.reject,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(ActivityRejectedNotification),
            ]
        ),

        TransitionTrigger(
            CollectActivityStateMachine.succeed,
            effects=[
                NotificationEffect(ActivitySucceededNotification),
            ]
        ),

        TransitionTrigger(
            CollectActivityStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(ActivityCancelledNotification),
            ]
        ),

        TransitionTrigger(
            CollectActivityStateMachine.restore,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.reset),
                NotificationEffect(ActivityRestoredNotification),
            ]
        ),

        ModelChangedTrigger(
            'realized',
            effects=[SetOverallContributor]
        )
    ]


def activity_is_finished(effect):
    """activity is finished"""
    return (
        effect.instance.activity.end and
        effect.instance.activity.end < date.today()
    )


def activity_will_be_empty(effect):
    """activity will be empty"""
    return len(
        effect.instance.activity.contributors.instance_of(
            CollectContributor
        ).filter(
            status=CollectContributorStateMachine.succeeded
        )
    ) == 1


def is_not_user(effect):
    """
    User is not the participant
    """
    if 'user' in effect.options:
        return effect.instance.user != effect.options['user']
    return False


def is_user(effect):
    """
    User is not the participant
    """
    if 'user' in effect.options:
        return effect.instance.user == effect.options['user']
    return False


def is_not_owner(effect):
    """
    User is not the owner
    """
    if 'user' in effect.options:
        return effect.instance.activity.owner != effect.options['user']
    return True


def team_is_active(effect):
    """Team status is open, or there is no team"""
    return (
        effect.instance.team.status == TeamStateMachine.open.value
        if effect.instance.team
        else True
    )


def is_team_activity(effect):
    """Team status is open, or there is no team"""
    return effect.instance.accepted_invite and effect.instance.accepted_invite.contributor.team


def is_not_team_activity(effect):
    """Team status is open, or there is no team"""
    return not effect.instance.team


@register(CollectContributor)
class CollectContributorTriggers(ContributorTriggers):
    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            CollectContributorStateMachine.initiate,
            effects=[
                TransitionEffect(
                    CollectContributorStateMachine.succeed,
                ),
                CreateCollectContribution,
                NotificationEffect(
                    ParticipantAddedNotification,
                    conditions=[is_not_user]
                ),
                NotificationEffect(
                    TeamMemberAddedMessage,
                    conditions=[
                        is_team_activity
                    ]
                ),
                NotificationEffect(
                    ParticipantAddedOwnerNotification,
                    conditions=[is_not_user, is_not_owner]
                ),
                NotificationEffect(
                    ParticipantJoinedNotification,
                    conditions=[is_user]
                ),
                NotificationEffect(
                    NewParticipantNotification,
                    conditions=[is_user]
                ),
                CreateTeamEffect,
                CreateInviteEffect
            ]
        ),
        TransitionTrigger(
            CollectContributorStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    CollectActivityStateMachine.expire,
                    conditions=[activity_is_finished, activity_will_be_empty]
                ),
                RelatedTransitionEffect('contributions', CollectContributionStateMachine.fail),
                NotificationEffect(ParticipantRemovedNotification, conditions=[is_not_team_activity]),
                NotificationEffect(TeamParticipantRemovedNotification, conditions=[is_team_activity]),
                NotificationEffect(ParticipantRemovedOwnerNotification),
                NotificationEffect(TeamMemberRemovedMessage),
            ]
        ),

        TransitionTrigger(
            CollectContributorStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    CollectActivityStateMachine.succeed,
                    conditions=[activity_is_finished]
                ),
            ]
        ),

        TransitionTrigger(
            CollectContributorStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect('contributions', CollectContributionStateMachine.fail),
                NotificationEffect(ParticipantWithdrewNotification),
                NotificationEffect(ParticipantWithdrewConfirmationNotification),
                NotificationEffect(TeamMemberWithdrewMessage),
            ]
        ),

        TransitionTrigger(
            CollectContributorStateMachine.reapply,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    CollectActivityStateMachine.expire,
                    conditions=[activity_is_finished]
                ),
                TransitionEffect(
                    CollectContributorStateMachine.succeed,
                    conditions=[team_is_active]
                ),

                NotificationEffect(ParticipantJoinedNotification)
            ]
        ),

        TransitionTrigger(
            CollectContributorStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    CollectContributionStateMachine.succeed,
                    conditions=[team_is_active]
                ),
            ]
        ),

    ]


@register(CollectContribution)
class CollectContributionTriggers(ContributionTriggers):
    triggers = ContributionTriggers.triggers + [
        TransitionTrigger(
            CollectContributionStateMachine.initiate,
            effects=[
                TransitionEffect(
                    CollectContributionStateMachine.succeed,
                ),
            ]
        ),

        TransitionTrigger(
            CollectContributionStateMachine.reset,
            effects=[
                TransitionEffect(
                    CollectContributionStateMachine.succeed,
                ),
            ]
        ),
    ]


TeamTriggers.triggers += [
    TransitionTrigger(
        TeamStateMachine.reopen,
        effects=[
            RelatedTransitionEffect(
                'members', CollectContributorStateMachine.succeed
            )
        ]
    )
]
