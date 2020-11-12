from django.utils import timezone

from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.fsm.triggers import ModelChangedTrigger, ModelDeletedTrigger, TransitionTrigger, register

from bluebottle.activities.triggers import ActivityTriggers, IntentionTriggers

from bluebottle.events.effects import SetTimeSpent, ResetTimeSpent
from bluebottle.follow.effects import (
    FollowActivityEffect, UnFollowActivityEffect
)

from bluebottle.events.messages import (
    EventSucceededOwnerMessage,
    EventRejectedOwnerMessage,
    ParticipantRejectedMessage,
    ParticipantApplicationMessage,
    ParticipantApplicationManagerMessage,
    EventCancelledMessage,
    EventExpiredMessage,
)
from bluebottle.events.models import Event, Participant
from bluebottle.events.messages import EventDateChanged
from bluebottle.events.states import EventStateMachine, ParticipantStateMachine


def event_is_full(effect):
    "the event is full"
    return effect.instance.capacity == len(effect.instance.participants)


def event_is_not_full(effect):
    "the event is not full"
    return effect.instance.capacity > len(effect.instance.participants)


def event_should_finish(effect):
    "the end time has passed"
    if isinstance(effect.instance, Participant):
        instance = effect.instance.activity
    else:
        instance = effect.instance

    return instance.current_end and instance.current_end < timezone.now()


def event_should_start(effect):
    "the start time has passed"
    return effect.instance.start and effect.instance.start < timezone.now() and not event_should_finish(effect)


def event_should_open(effect):
    "the start time has not passed"
    return effect.instance.start and effect.instance.start > timezone.now()


def event_has_participants(effect):
    """there are participants"""
    return len(effect.instance.participants) > 0


def event_has_no_participants(effect):
    """there are no participants"""
    return len(effect.instance.participants) == 0


def initiative_is_approved(effect):
    return effect.instance.initiative.status == 'approved'


def event_will_become_full(effect):
    "event will be full"
    activity = effect.instance.activity
    return activity.capacity == len(activity.participants) + 1


def event_will_become_open(effect):
    "event will not be full"
    activity = effect.instance.activity
    return activity.capacity == len(activity.participants)


def event_is_finished(effect):
    "event is finished"
    return effect.instance.activity.current_end < timezone.now()


def event_is_not_finished(effect):
    "event is not finished"
    return not effect.instance.activity.start < timezone.now()


def event_will_be_empty(effect):
    "event will be empty"
    return effect.instance.activity.participants.exclude(id=effect.instance.id).count() == 0


def not_triggered_by_user(effect):
    "The participant is different from the current user"
    return 'user' not in effect.options or effect.options['user'] != effect.instance.user


@register(Event)
class EventTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [
        TransitionTrigger(
            EventStateMachine.submit,
            effects=[
                TransitionEffect(
                    EventStateMachine.auto_approve,
                    conditions=[initiative_is_approved, event_should_open]
                ),
                TransitionEffect(
                    EventStateMachine.expire,
                    conditions=[event_should_finish, event_has_no_participants]
                ),
            ]
        ),

        TransitionTrigger(
            EventStateMachine.auto_approve,
            effects=[
                TransitionEffect(
                    EventStateMachine.expire,
                    conditions=[event_should_start, event_has_no_participants]
                ),
                TransitionEffect(
                    EventStateMachine.expire,
                    conditions=[event_should_finish, event_has_no_participants]
                ),
                TransitionEffect(
                    EventStateMachine.succeed,
                    conditions=[event_should_finish, event_has_participants]
                ),
            ]
        ),

        TransitionTrigger(
            EventStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('participants', ParticipantStateMachine.fail),
                NotificationEffect(EventCancelledMessage),
            ]
        ),

        TransitionTrigger(
            EventStateMachine.reschedule,
            effects=[
                RelatedTransitionEffect('participants', ParticipantStateMachine.reset),
            ]
        ),

        TransitionTrigger(
            EventStateMachine.expire,
            effects=[
                NotificationEffect(EventExpiredMessage),
            ]
        ),

        TransitionTrigger(
            EventStateMachine.succeed,
            effects=[
                NotificationEffect(EventSucceededOwnerMessage),
                RelatedTransitionEffect('participants', ParticipantStateMachine.succeed)
            ]
        ),

        TransitionTrigger(
            EventStateMachine.reject,
            effects=[
                NotificationEffect(EventRejectedOwnerMessage),
            ]
        ),

        TransitionTrigger(
            EventStateMachine.restore,
            effects=[
                RelatedTransitionEffect('all_participants', ParticipantStateMachine.reset),
            ]
        ),
        ModelChangedTrigger(
            'capacity',
            effects=[
                TransitionEffect(EventStateMachine.reopen, conditions=[
                    event_should_open,
                    event_is_not_full
                ]),
                TransitionEffect(EventStateMachine.lock, conditions=[
                    event_should_open,
                    event_is_full
                ]),
            ]
        ),
        ModelChangedTrigger(
            'start',
            effects=[

                NotificationEffect(
                    EventDateChanged,
                    conditions=[
                        event_should_open
                    ]
                ),
                TransitionEffect(
                    EventStateMachine.succeed,
                    conditions=[
                        event_should_finish,
                        event_has_participants
                    ]
                ),
                TransitionEffect(
                    EventStateMachine.start,
                    conditions=[
                        event_should_start,
                        event_has_participants
                    ]
                ),
                TransitionEffect(
                    EventStateMachine.expire,
                    conditions=[
                        event_should_start,
                        event_has_no_participants
                    ]
                ),
                TransitionEffect(
                    EventStateMachine.expire,
                    conditions=[
                        event_should_finish,
                        event_has_no_participants
                    ]
                ),
                TransitionEffect(
                    EventStateMachine.reschedule,
                    conditions=[
                        event_should_open
                    ]
                ),
                TransitionEffect(
                    EventStateMachine.lock,
                    conditions=[
                        event_is_full
                    ]
                ),
            ]
        )

    ]


@register(Participant)
class ParticpantTriggers(IntentionTriggers):
    triggers = [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[

                TransitionEffect(
                    ParticipantStateMachine.succeed,
                    conditions=[event_should_finish]
                ),
                RelatedTransitionEffect(
                    'activity',
                    EventStateMachine.lock,
                    conditions=[event_will_become_full]
                ),
                NotificationEffect(ParticipantApplicationManagerMessage),
                NotificationEffect(ParticipantApplicationMessage, conditions=[not_triggered_by_user]),
                FollowActivityEffect,
            ]
        ),
        TransitionTrigger(
            ParticipantStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    EventStateMachine.reopen,
                    conditions=[event_will_become_open]
                ),
                UnFollowActivityEffect
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.reapply,
            effects=[
                TransitionEffect(
                    ParticipantStateMachine.succeed,
                    conditions=[event_should_finish]
                ),
                RelatedTransitionEffect(
                    'activity',
                    EventStateMachine.lock,
                    conditions=[event_will_become_full]
                ),
                NotificationEffect(ParticipantApplicationManagerMessage),
                NotificationEffect(ParticipantApplicationMessage),
                FollowActivityEffect
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.reject,
            effects=[
                RelatedTransitionEffect('activity', EventStateMachine.reopen),
                NotificationEffect(ParticipantRejectedMessage),
                UnFollowActivityEffect
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.accept,
            effects=[

                TransitionEffect(
                    ParticipantStateMachine.succeed, conditions=[event_should_finish]
                ),
                RelatedTransitionEffect(
                    'activity',
                    EventStateMachine.lock,
                    conditions=[event_will_become_full]
                ),
                NotificationEffect(ParticipantApplicationMessage),
                FollowActivityEffect
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.mark_present,
            effects=[
                SetTimeSpent,
                FollowActivityEffect,
                RelatedTransitionEffect(
                    'activity',
                    EventStateMachine.succeed,
                    conditions=[event_should_finish]
                )
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.succeed,
            effects=[
                SetTimeSpent,
                RelatedTransitionEffect(
                    'activity', EventStateMachine.succeed,
                )
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.reset,
            effects=[
                ResetTimeSpent,
                FollowActivityEffect
            ]
        ),
        TransitionTrigger(
            ParticipantStateMachine.fail,
            effects=[ResetTimeSpent, UnFollowActivityEffect]
        ),
        TransitionTrigger(
            ParticipantStateMachine.mark_absent,

            effects=[
                ResetTimeSpent,
                RelatedTransitionEffect(
                    'activity',
                    EventStateMachine.expire,
                    conditions=[event_is_finished, event_will_be_empty]
                ),
                UnFollowActivityEffect
            ]
        ),
        ModelDeletedTrigger(
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    EventStateMachine.cancel,
                    conditions=[
                        event_should_finish,
                        event_will_be_empty
                    ]
                ),
                RelatedTransitionEffect(
                    'activity',
                    EventStateMachine.reopen,
                    conditions=[
                        event_will_become_open,
                        event_is_not_finished
                    ],
                ),
            ]

        )

    ]
