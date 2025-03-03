from datetime import date

from bluebottle.activities.messages import (
    ActivityExpiredNotification, ActivitySucceededNotification,
    ActivityRejectedNotification, ActivityCancelledNotification,
    ActivityRestoredNotification, InactiveParticipantAddedNotification, ParticipantWithdrewConfirmationNotification,
)
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.activities.triggers import (
    ActivityTriggers, ContributorTriggers, ContributionTriggers
)
from bluebottle.collect.effects import CreateCollectContribution
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
from bluebottle.time_based.messages import (
    ParticipantWithdrewNotification, ParticipantRemovedNotification, ParticipantRemovedOwnerNotification,
    NewParticipantNotification, ManagerParticipantAddedOwnerNotification,
    ParticipantAddedNotification
)


def is_finished(effect):
    """
    has finished
    """
    return (
        effect.instance.end and
        effect.instance.end < date.today()
    )


def is_started(effect):
    """
    is started
    """
    return (
        not effect.instance.start or
        effect.instance.start <= date.today()
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


def has_no_end_date(effect):
    """has no end date"""
    return not effect.instance.end


@register(CollectActivity)
class CollectActivityTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [
        ModelChangedTrigger(
            'start',
            effects=[
                RelatedTransitionEffect(
                    'active_contributors',
                    CollectContributorStateMachine.succeed,
                    conditions=[is_started]
                ),
            ]
        ),

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
    ]


def activity_is_finished(effect):
    """activity is finished"""
    return (
        effect.instance.activity.end and
        effect.instance.activity.end < date.today()
    )


def activity_is_started(effect):
    """activity is started"""
    return (
        not effect.instance.activity.start or
        effect.instance.activity.start < date.today()
    )


def activity_is_not_started(effect):
    """activity is not started"""
    return (
        effect.instance.activity.start and
        effect.instance.activity.start > date.today()
    )


def activity_will_be_empty(effect):
    """activity will be empty"""
    return (
        len(
            effect.instance.activity.contributors.instance_of(
                CollectContributor
            ).filter(status=CollectContributorStateMachine.succeeded.value)
        )
    ) < 2


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


def contributor_activity_started(effect):
    """activity is started"""
    return (
        not effect.instance.contributor.activity.start or
        effect.instance.contributor.activity.start < date.today()
    )


@register(CollectContribution)
class CollectContributionTriggers(ContributionTriggers):
    triggers = ContributionTriggers.triggers + [
        TransitionTrigger(
            CollectContributionStateMachine.initiate,
            effects=[
                TransitionEffect(
                    CollectContributionStateMachine.succeed,
                    conditions=[contributor_activity_started]
                ),
            ]
        ),
    ]


def participant_is_active(effect):
    return effect.instance.user.is_active


def participant_is_inactive(effect):
    return not effect.instance.user.is_active


@register(CollectContributor)
class CollectContributorTriggers(ContributorTriggers):
    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            CollectContributorStateMachine.initiate,
            effects=[
                TransitionEffect(
                    CollectContributorStateMachine.succeed,
                    conditions=[activity_is_started]
                ),
                TransitionEffect(
                    CollectContributorStateMachine.accept,
                    conditions=[activity_is_not_started]
                ),
                CreateCollectContribution,
                NotificationEffect(
                    ParticipantAddedNotification,
                    conditions=[is_not_user, participant_is_active]
                ),
                NotificationEffect(
                    InactiveParticipantAddedNotification,
                    conditions=[is_not_user, participant_is_inactive]
                ),
                NotificationEffect(
                    ManagerParticipantAddedOwnerNotification,
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
                NotificationEffect(ParticipantRemovedNotification),
                NotificationEffect(ParticipantRemovedOwnerNotification),
            ]
        ),

        TransitionTrigger(
            CollectContributorStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    CollectActivityStateMachine.expire,
                    conditions=[activity_is_finished, activity_will_be_empty]
                ),
                RelatedTransitionEffect('contributions', CollectContributionStateMachine.fail),
                NotificationEffect(ParticipantWithdrewNotification),
                NotificationEffect(ParticipantWithdrewConfirmationNotification),
            ]
        ),

        TransitionTrigger(
            CollectContributorStateMachine.reapply,
            effects=[
                TransitionEffect(
                    CollectContributorStateMachine.succeed,
                ),
                NotificationEffect(ParticipantJoinedNotification)
            ]
        ),

        TransitionTrigger(
            CollectContributorStateMachine.re_accept,
            effects=[
                TransitionEffect(
                    CollectContributorStateMachine.succeed,
                ),
                NotificationEffect(ParticipantAddedNotification)
            ]
        ),

        TransitionTrigger(
            CollectContributorStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    CollectContributionStateMachine.succeed,
                ),
                RelatedTransitionEffect(
                    'activity',
                    CollectActivityStateMachine.succeed,
                    conditions=[activity_is_finished]
                ),

            ]
        ),

    ]
