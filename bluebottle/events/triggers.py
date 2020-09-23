from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.fsm.triggers import ModelChangedTrigger, ModelDeletedTrigger, TransitionTrigger, register

from bluebottle.activities.effects import CreateOrganizer

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
from bluebottle.activities.states import OrganizerStateMachine


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
class InitiateTrigger(TransitionTrigger):
    transition = EventStateMachine.initiate

    effects = [CreateOrganizer]


@register(Event)
class SubmitEventTrigger(TransitionTrigger):
    transition = EventStateMachine.submit

    effects = [
        TransitionEffect(
            EventStateMachine.auto_approve,
            conditions=[
                initiative_is_approved,
                event_should_open
            ]
        ),
        TransitionEffect(
            EventStateMachine.expire,
            conditions=[event_should_finish, event_has_no_participants]
        ),
        TransitionEffect(
            OrganizerStateMachine.succeed,
            conditions=[event_should_finish, event_has_participants]
        ),
    ]


@register(Event)
class ApproveEventTrigger(TransitionTrigger):
    transition = EventStateMachine.auto_approve

    effects = [
        RelatedTransitionEffect('organizer', OrganizerStateMachine.succeed),
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


@register(Event)
class CancelEventTrigger(TransitionTrigger):
    transition = EventStateMachine.cancel

    effects = [
        RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
        RelatedTransitionEffect('participants', ParticipantStateMachine.fail),
        NotificationEffect(EventCancelledMessage),
    ]


@register(Event)
class RescheduleEventTrigger(TransitionTrigger):
    transition = EventStateMachine.reschedule

    effects = [
        RelatedTransitionEffect('participants', ParticipantStateMachine.reset),
    ]


@register(Event)
class ExpireEventTrigger(TransitionTrigger):
    transition = EventStateMachine.expire

    effects = [
        NotificationEffect(EventExpiredMessage),
    ]


@register(Event)
class SucceedEventTrigger(TransitionTrigger):
    transition = EventStateMachine.succeed

    effects = [
        NotificationEffect(EventSucceededOwnerMessage),
        RelatedTransitionEffect('participants', ParticipantStateMachine.succeed)
    ]


@register(Event)
class RejectEventTrigger(TransitionTrigger):
    transition = EventStateMachine.reject

    effects = [
        RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
        NotificationEffect(EventRejectedOwnerMessage),
    ]


@register(Event)
class RestoreEventTrigger(TransitionTrigger):
    transition = EventStateMachine.restore

    effects = [
        RelatedTransitionEffect('organizer', OrganizerStateMachine.reset),
        RelatedTransitionEffect('participants', OrganizerStateMachine.reset),
    ]


@register(Participant)
class InitiateParticipantTrigger(TransitionTrigger):
    transition = ParticipantStateMachine.initiate

    effects = [
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


@register(Participant)
class WithdrawParticipantTrigger(TransitionTrigger):
    transition = ParticipantStateMachine.withdraw

    effects = [
        RelatedTransitionEffect(
            'activity',
            EventStateMachine.reopen,
            conditions=[event_will_become_open]
        ),
        UnFollowActivityEffect
    ]


@register(Participant)
class ReapplyParticipantTrigger(TransitionTrigger):
    transition = ParticipantStateMachine.reapply

    effects = [
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


@register(Participant)
class RejectParticipantTrigger(TransitionTrigger):
    transition = ParticipantStateMachine.reject

    effects = [
        RelatedTransitionEffect('activity', EventStateMachine.reopen),
        NotificationEffect(ParticipantRejectedMessage),
        UnFollowActivityEffect
    ]


@register(Participant)
class AcceptParticipantTrigger(TransitionTrigger):
    transition = ParticipantStateMachine.accept

    effects = [
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


@register(Participant)
class MarkPresentParticipantTrigger(TransitionTrigger):
    transition = ParticipantStateMachine.mark_present

    effects = [
        SetTimeSpent,
        FollowActivityEffect,
        RelatedTransitionEffect(
            'activity',
            EventStateMachine.succeed,
            conditions=[event_should_finish]
        )
    ]


@register(Participant)
class SucceedParticipantTrigger(TransitionTrigger):
    transition = ParticipantStateMachine.succeed
    effects = [
        SetTimeSpent,
        RelatedTransitionEffect(
            'activity', EventStateMachine.succeed,
        )
    ]


@register(Participant)
class ResetParticipantTrigger(TransitionTrigger):
    transition = ParticipantStateMachine.reset

    effects = [ResetTimeSpent, FollowActivityEffect]


@register(Participant)
class FailParticipantTrigger(TransitionTrigger):
    transition = ParticipantStateMachine.fail

    effects = [ResetTimeSpent, UnFollowActivityEffect]


@register(Participant)
class MarkAbsentParticipantTrigger(TransitionTrigger):
    transition = ParticipantStateMachine.mark_absent

    effects = [
        ResetTimeSpent,
        RelatedTransitionEffect(
            'activity',
            EventStateMachine.expire,
            conditions=[event_is_finished, event_will_be_empty]
        ),
        UnFollowActivityEffect
    ]


@register(Event)
class CapacityChangedTrigger(ModelChangedTrigger):
    field = 'capacity'

    effects = [
        TransitionEffect(EventStateMachine.reopen, conditions=[
            event_should_open,
            event_is_not_full
        ]),
        TransitionEffect(EventStateMachine.lock, conditions=[
            event_should_open,
            event_is_full
        ]),
    ]


@register(Event)
class DateChangedTrigger(ModelChangedTrigger):
    field = 'start'

    effects = [
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


@ register(Participant)
class ParticipantDeletedTrigger(ModelDeletedTrigger):
    title = _('delete this participant')
    field = 'start'

    effects = [
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

    def __unicode__(self):
        return unicode(_("Participant has been deleted"))
