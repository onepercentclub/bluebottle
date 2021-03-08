from datetime import date

from bluebottle.activities.messages import ActivityExpiredNotification, ActivitySucceededNotification, \
    ActivityRejectedNotification, ActivityCancelledNotification, ActivityRestoredNotification
from bluebottle.deeds.messages import DeedDateChangedNotification
from bluebottle.notifications.effects import NotificationEffect

from bluebottle.activities.triggers import (
    ActivityTriggers, ContributorTriggers
)

from bluebottle.activities.states import EffortContributionStateMachine, OrganizerStateMachine
from bluebottle.activities.effects import CreateEffortContribution

from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.deeds.states import (
    DeedStateMachine, DeedParticipantStateMachine
)
from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import (
    register, TransitionTrigger, ModelChangedTrigger
)
from bluebottle.time_based.messages import ParticipantRemovedNotification, ParticipantFinishedNotification, \
    ParticipantWithdrewNotification, NewParticipantNotification, ParticipantAddedOwnerNotification, \
    ParticipantRemovedOwnerNotification, ParticipantAddedNotification
from bluebottle.time_based.triggers import is_not_owner, is_not_user, is_user


def is_started(effect):
    """
    has started
    """
    return (
        effect.instance.start and
        effect.instance.start < date.today()
    )


def is_not_started(effect):
    """
    hasn't started yet
    """
    return not is_started(effect)


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


def has_participants(effect):
    """ has participants"""
    return len(effect.instance.participants) > 0


def has_no_participants(effect):
    """ has accepted participants"""
    return not has_participants(effect)


def has_no_start_date(effect):
    """ has accepted participants"""
    return not effect.instance.start


def has_no_end_date(effect):
    """ has accepted participants"""
    return not effect.instance.end


@register(Deed)
class DeedTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [
        ModelChangedTrigger(
            'end',
            effects=[
                TransitionEffect(DeedStateMachine.restart, conditions=[is_started]),
                TransitionEffect(DeedStateMachine.reopen, conditions=[is_not_started]),
                TransitionEffect(DeedStateMachine.succeed, conditions=[is_finished, has_participants]),
                TransitionEffect(DeedStateMachine.expire, conditions=[is_finished, has_no_participants]),
                NotificationEffect(
                    DeedDateChangedNotification,
                    conditions=[
                        is_not_finished
                    ]
                )
            ]
        ),

        ModelChangedTrigger(
            'start',
            effects=[
                TransitionEffect(DeedStateMachine.start, conditions=[is_started]),
                TransitionEffect(DeedStateMachine.reopen, conditions=[is_not_started]),
                NotificationEffect(
                    DeedDateChangedNotification,
                    conditions=[
                        is_not_started
                    ]
                )
            ]
        ),

        TransitionTrigger(
            DeedStateMachine.start,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    DeedParticipantStateMachine.succeed,
                    conditions=[has_no_end_date]
                ),
            ]
        ),

        TransitionTrigger(
            DeedStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    DeedParticipantStateMachine.succeed
                ),
                NotificationEffect(ActivitySucceededNotification)
            ]
        ),

        TransitionTrigger(
            DeedStateMachine.expire,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(ActivityExpiredNotification)
            ]
        ),

        TransitionTrigger(
            DeedStateMachine.reject,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(ActivityRejectedNotification),
            ]
        ),

        TransitionTrigger(
            DeedStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(ActivityCancelledNotification),
            ]
        ),

        TransitionTrigger(
            DeedStateMachine.restore,
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
    """activity is finished"""
    return (
        effect.instance.activity.start and
        effect.instance.activity.start < date.today()
    )


def activity_will_be_empty(effect):
    """activity will be empty"""
    return len(effect.instance.activity.participants) == 1


def activity_has_no_start(effect):
    """activity has no start"""
    return not effect.instance.activity.start


def activity_has_no_end(effect):
    """activity has no start"""
    return not effect.instance.activity.end


@register(DeedParticipant)
class DeedParticipantTriggers(ContributorTriggers):
    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            DeedParticipantStateMachine.initiate,
            effects=[
                TransitionEffect(
                    DeedParticipantStateMachine.succeed,
                    conditions=[activity_has_no_start, activity_has_no_end]
                ),
                CreateEffortContribution,
                NotificationEffect(
                    NewParticipantNotification,
                    conditions=[is_user]
                ),
                NotificationEffect(
                    ParticipantAddedNotification,
                    conditions=[is_not_user]
                ),
                NotificationEffect(
                    ParticipantAddedOwnerNotification,
                    conditions=[is_not_user, is_not_owner]
                )

            ]
        ),
        TransitionTrigger(
            DeedParticipantStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    DeedStateMachine.expire,
                    conditions=[activity_is_finished, activity_will_be_empty]
                ),
                RelatedTransitionEffect('contributions', EffortContributionStateMachine.fail),
                NotificationEffect(ParticipantRemovedNotification),
                NotificationEffect(
                    ParticipantRemovedOwnerNotification,
                    conditions=[is_not_owner]
                )
            ]
        ),

        TransitionTrigger(
            DeedParticipantStateMachine.accept,
            effects=[
                TransitionEffect(
                    DeedParticipantStateMachine.succeed,
                    conditions=[activity_has_no_start, activity_has_no_end]
                ),
                TransitionEffect(
                    DeedParticipantStateMachine.succeed,
                    conditions=[activity_is_started, activity_has_no_end]
                ),
                TransitionEffect(
                    DeedParticipantStateMachine.succeed,
                    conditions=[activity_is_finished]
                ),
            ]
        ),
        TransitionTrigger(
            DeedParticipantStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect('contributions', EffortContributionStateMachine.fail),
                NotificationEffect(ParticipantWithdrewNotification),
            ]
        ),

        TransitionTrigger(
            DeedParticipantStateMachine.reapply,
            effects=[
                TransitionEffect(
                    DeedParticipantStateMachine.succeed,
                    conditions=[activity_has_no_start, activity_has_no_end]
                ),
                TransitionEffect(
                    DeedParticipantStateMachine.succeed,
                    conditions=[activity_is_started, activity_has_no_end]
                ),
            ]
        ),

        TransitionTrigger(
            DeedParticipantStateMachine.succeed,
            effects=[
                RelatedTransitionEffect('contributions', EffortContributionStateMachine.succeed),
                NotificationEffect(ParticipantFinishedNotification),
            ]
        ),
        TransitionTrigger(
            DeedParticipantStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    DeedStateMachine.succeed,
                    conditions=[activity_is_finished]
                ),
            ]
        ),
    ]
