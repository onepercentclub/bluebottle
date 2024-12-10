from datetime import date

from bluebottle.activities.messages import (
    ActivityExpiredNotification, ActivitySucceededNotification,
    ActivityRejectedNotification, ActivityCancelledNotification,
    ActivityRestoredNotification, ParticipantWithdrewConfirmationNotification,
)
from bluebottle.activities.states import (
    OrganizerStateMachine, EffortContributionStateMachine
)
from bluebottle.activities.triggers import (
    ActivityTriggers, ContributorTriggers, has_organizer
)
from bluebottle.deeds.effects import CreateEffortContribution, RescheduleEffortsEffect, SetEndDateEffect
from bluebottle.deeds.messages import (
    DeedDateChangedNotification,
    ParticipantJoinedNotification
)
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.deeds.states import (
    DeedStateMachine, DeedParticipantStateMachine
)

from bluebottle.events.effects import TriggerEvent

from bluebottle.follow.effects import (
    FollowActivityEffect, UnFollowActivityEffect
)
from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import (
    register, TransitionTrigger, ModelChangedTrigger
)
from bluebottle.impact.effects import UpdateImpactGoalsForActivityEffect
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.messages import (
    ParticipantRemovedNotification,
    ParticipantWithdrewNotification,
    NewParticipantNotification, ManagerParticipantAddedOwnerNotification,
    ParticipantRemovedOwnerNotification, ParticipantAddedNotification
)
from bluebottle.time_based.triggers.triggers import is_not_owner, is_not_user, is_user


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
    """ has no participants"""
    return not has_participants(effect)


def has_no_start_date(effect):
    """ has no start date"""
    return not effect.instance.start


def has_start_date(effect):
    """ has start date"""
    return effect.instance.start


def has_no_end_date(effect):
    """ has no end date"""
    return not effect.instance.end


@register(Deed)
class DeedTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [
        ModelChangedTrigger(
            'end',
            effects=[
                TransitionEffect(DeedStateMachine.reopen, conditions=[is_not_finished]),
                TransitionEffect(DeedStateMachine.succeed, conditions=[is_finished, has_participants]),
                TransitionEffect(DeedStateMachine.expire, conditions=[is_finished, has_no_participants]),
                RescheduleEffortsEffect,
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
                RelatedTransitionEffect(
                    'participants',
                    DeedParticipantStateMachine.re_accept,
                    conditions=[has_start_date, is_not_started]
                ),
                RelatedTransitionEffect(
                    'participants',
                    DeedParticipantStateMachine.succeed,
                    conditions=[is_started]
                ),
                RescheduleEffortsEffect,
                NotificationEffect(
                    DeedDateChangedNotification,
                    conditions=[
                        is_not_started
                    ]
                )
            ]
        ),

        ModelChangedTrigger(
            'target',
            effects=[UpdateImpactGoalsForActivityEffect]
        ),

        TransitionTrigger(
            DeedStateMachine.auto_approve,
            effects=[
                TransitionEffect(DeedStateMachine.reopen, conditions=[is_not_finished]),
                TransitionEffect(DeedStateMachine.succeed, conditions=[is_finished, has_participants]),
                TransitionEffect(DeedStateMachine.expire, conditions=[is_finished, has_no_participants]),
            ]
        ),
        TransitionTrigger(
            DeedStateMachine.publish,
            effects=[
                TransitionEffect(DeedStateMachine.reopen, conditions=[is_not_finished]),
                TransitionEffect(DeedStateMachine.succeed, conditions=[is_finished, has_participants]),
                TransitionEffect(DeedStateMachine.expire, conditions=[is_finished, has_no_participants]),
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.succeed,
                    conditions=[has_organizer]
                ),
                TriggerEvent('deed.published')
            ]
        ),

        TransitionTrigger(
            DeedStateMachine.reopen,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    DeedParticipantStateMachine.re_accept,
                    conditions=[is_not_finished]
                ),
            ]
        ),

        TransitionTrigger(
            DeedStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    DeedParticipantStateMachine.succeed,
                    conditions=[is_not_started]
                ),
                NotificationEffect(ActivitySucceededNotification),
                SetEndDateEffect,
                TriggerEvent('deed.succeeded')
            ]
        ),

        TransitionTrigger(
            DeedStateMachine.expire,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(ActivityExpiredNotification),
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


def activity_expired(effect):
    """activity was unsuccessful"""
    return (
        effect.instance.activity.status == 'expired'
    )


def activity_not_expired(effect):
    """activity did not expire"""
    return not activity_expired(effect)


def activity_did_start(effect):
    """activity start date in the past"""
    return (
        not effect.instance.activity.start or
        effect.instance.activity.start < date.today()
    )


def activity_will_be_empty(effect):
    """activity will be empty"""
    return len(effect.instance.activity.participants) == 1


def activity_has_no_end(effect):
    """activity has no start"""
    return not effect.instance.activity.end


def contributor_is_active(effect):
    """Contributor status is new"""
    return effect.instance.status == DeedParticipantStateMachine.new.value


@register(DeedParticipant)
class DeedParticipantTriggers(ContributorTriggers):
    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            DeedParticipantStateMachine.initiate,
            effects=[
                TransitionEffect(
                    DeedParticipantStateMachine.succeed,
                    conditions=[activity_did_start]
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
                    ManagerParticipantAddedOwnerNotification,
                    conditions=[is_not_user, is_not_owner]
                ),
                NotificationEffect(
                    ParticipantJoinedNotification,
                    conditions=[is_user]
                ),
                FollowActivityEffect,
                TriggerEvent('deed-participant.succeeded')
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
                NotificationEffect(
                    ParticipantRemovedOwnerNotification,
                    conditions=[is_not_owner]
                ),
                NotificationEffect(
                    ParticipantRemovedNotification,
                    conditions=[is_not_owner]
                ),
                UnFollowActivityEffect
            ]
        ),

        TransitionTrigger(
            DeedParticipantStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    DeedStateMachine.succeed,
                    conditions=[activity_is_finished]
                ),
                RelatedTransitionEffect(
                    'contributions',
                    EffortContributionStateMachine.succeed,
                    conditions=[contributor_is_active]
                ),
            ]
        ),

        TransitionTrigger(
            DeedParticipantStateMachine.accept,
            effects=[
                TransitionEffect(
                    DeedParticipantStateMachine.succeed,
                    conditions=[activity_did_start]
                ),
                RelatedTransitionEffect(
                    'activity',
                    DeedStateMachine.succeed,
                    conditions=[activity_is_finished, activity_expired]
                ),
            ]
        ),
        TransitionTrigger(
            DeedParticipantStateMachine.re_accept,
            effects=[
                RelatedTransitionEffect('contributions', EffortContributionStateMachine.reset),
                FollowActivityEffect
            ]
        ),
        TransitionTrigger(
            DeedParticipantStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect('contributions', EffortContributionStateMachine.fail),
                NotificationEffect(ParticipantWithdrewNotification),
                NotificationEffect(ParticipantWithdrewConfirmationNotification),
                UnFollowActivityEffect
            ]
        ),

        TransitionTrigger(
            DeedParticipantStateMachine.reapply,
            effects=[
                RelatedTransitionEffect('contributions', EffortContributionStateMachine.reset),
                TransitionEffect(
                    DeedParticipantStateMachine.succeed,
                    conditions=[activity_did_start, ]
                ),
                FollowActivityEffect,
            ]
        ),

        TransitionTrigger(
            DeedParticipantStateMachine.succeed,
            effects=[
                RelatedTransitionEffect('contributions', EffortContributionStateMachine.succeed),
            ]
        ),
    ]
