from datetime import date

from bluebottle.activities.messages import ActivityExpiredNotification, ActivitySucceededNotification, \
    ActivityRejectedNotification, ActivityCancelledNotification, ActivityRestoredNotification
from bluebottle.activities.states import OrganizerStateMachine, EffortContributionStateMachine
from bluebottle.activities.triggers import (
    ActivityTriggers, ContributorTriggers
)
from bluebottle.deeds.effects import CreateEffortContribution, RescheduleEffortsEffect
from bluebottle.collect.messages import CollectActivityDateChangedNotification
from bluebottle.collect.models import CollectActivity, CollectContributor
from bluebottle.collect.states import (
    CollectActivityStateMachine, CollectContributorStateMachine
)
from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import (
    register, TransitionTrigger, ModelChangedTrigger
)
from bluebottle.notifications.effects import NotificationEffect
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


def has_contributors(effect):
    """ has contributors"""
    return len(effect.instance.accepted_contributors) > 0


def has_no_contributors(effect):
    """ has no contributors"""
    return not has_contributors(effect)


def has_no_start_date(effect):
    """has no start date"""
    return not effect.instance.start


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
            'end',
            effects=[
                TransitionEffect(CollectActivityStateMachine.reopen, conditions=[is_not_finished]),
                TransitionEffect(CollectActivityStateMachine.succeed, conditions=[is_finished, has_contributors]),
                TransitionEffect(CollectActivityStateMachine.expire, conditions=[is_finished, has_no_contributors]),
                RescheduleEffortsEffect,
                NotificationEffect(
                    CollectActivityDateChangedNotification,
                    conditions=[
                        is_not_finished
                    ]
                )
            ]
        ),

        ModelChangedTrigger(
            'start',
            effects=[
                RelatedTransitionEffect(
                    'contributors',
                    CollectContributorStateMachine.re_accept,
                    conditions=[has_start_date, is_not_started]
                ),
                RelatedTransitionEffect(
                    'contributors',
                    CollectContributorStateMachine.succeed,
                    conditions=[has_no_end_date, is_started]
                ),
                RescheduleEffortsEffect,
                NotificationEffect(
                    CollectActivityDateChangedNotification,
                    conditions=[
                        is_not_started
                    ]
                )
            ]
        ),

        TransitionTrigger(
            CollectActivityStateMachine.auto_approve,
            effects=[
                TransitionEffect(CollectActivityStateMachine.reopen, conditions=[is_not_finished]),
                TransitionEffect(CollectActivityStateMachine.succeed, conditions=[is_finished, has_contributors]),
                TransitionEffect(CollectActivityStateMachine.expire, conditions=[is_finished, has_no_contributors]),
            ]
        ),

        TransitionTrigger(
            CollectActivityStateMachine.reopen,
            effects=[
                RelatedTransitionEffect(
                    'contributors',
                    CollectContributorStateMachine.re_accept,
                    conditions=[is_not_finished]
                ),
            ]
        ),

        TransitionTrigger(
            CollectActivityStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'contributors',
                    CollectContributorStateMachine.succeed
                ),
                NotificationEffect(ActivitySucceededNotification)
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
    """activity is finished"""
    return (
        effect.instance.activity.start and
        effect.instance.activity.start < date.today()
    )


def activity_will_be_empty(effect):
    """activity will be empty"""
    return len(effect.instance.activity.contributors) == 1


def activity_has_no_start(effect):
    """activity has no start"""
    return not effect.instance.activity.start


def activity_has_no_end(effect):
    """activity has no start"""
    return not effect.instance.activity.end


@register(CollectContributor)
class CollectContributorTriggers(ContributorTriggers):
    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            CollectContributorStateMachine.initiate,
            effects=[
                TransitionEffect(
                    CollectContributorStateMachine.succeed,
                    conditions=[activity_has_no_start, activity_has_no_end]
                ),

                TransitionEffect(
                    CollectContributorStateMachine.succeed,
                    conditions=[activity_is_started, activity_has_no_end]
                ),

                TransitionEffect(
                    CollectContributorStateMachine.succeed,
                    conditions=[activity_is_finished]
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
            CollectContributorStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    CollectActivityStateMachine.expire,
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
            CollectContributorStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    CollectActivityStateMachine.succeed,
                    conditions=[activity_is_finished]
                ),
                RelatedTransitionEffect('contributions', EffortContributionStateMachine.succeed),
            ]
        ),

        TransitionTrigger(
            CollectContributorStateMachine.accept,
            effects=[
                TransitionEffect(
                    CollectContributorStateMachine.succeed,
                    conditions=[activity_has_no_start, activity_has_no_end]
                ),
                TransitionEffect(
                    CollectContributorStateMachine.succeed,
                    conditions=[activity_is_started, activity_has_no_end]
                ),
                TransitionEffect(
                    CollectContributorStateMachine.succeed,
                    conditions=[activity_is_finished]
                ),
            ]
        ),

        TransitionTrigger(
            CollectContributorStateMachine.re_accept,
            effects=[
                RelatedTransitionEffect('contributions', EffortContributionStateMachine.reset),
            ]
        ),
        TransitionTrigger(
            CollectContributorStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect('contributions', EffortContributionStateMachine.fail),
                NotificationEffect(ParticipantWithdrewNotification),
            ]
        ),

        TransitionTrigger(
            CollectContributorStateMachine.reapply,
            effects=[
                TransitionEffect(
                    CollectContributorStateMachine.succeed,
                    conditions=[activity_has_no_start, activity_has_no_end]
                ),
                TransitionEffect(
                    CollectContributorStateMachine.succeed,
                    conditions=[activity_is_started, activity_has_no_end]
                ),
            ]
        ),

        TransitionTrigger(
            CollectContributorStateMachine.succeed,
            effects=[
                RelatedTransitionEffect('contributions', EffortContributionStateMachine.succeed),
                NotificationEffect(ParticipantFinishedNotification),
            ]
        ),
        TransitionTrigger(
            CollectContributorStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    CollectActivityStateMachine.succeed,
                    conditions=[activity_is_finished]
                ),
            ]
        ),
    ]
