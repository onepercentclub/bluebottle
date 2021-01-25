from datetime import date

from django.utils.timezone import now

from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.activities.triggers import (
    ActivityTriggers, ContributorTriggers, ContributionTriggers
)
from bluebottle.follow.effects import (
    FollowActivityEffect, UnFollowActivityEffect
)
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import register, ModelChangedTrigger, TransitionTrigger, TriggerManager
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects import (
    CreatePeriodParticipationEffect, SetEndDateEffect,
    ClearStartEffect, ClearDeadlineEffect,
    RescheduleDurationsEffect,
    ActiveDurationsTransitionEffect, CreateSlotParticipantsForParticipantsEffect,
    CreateSlotParticipantsForSlotsEffect, CreateSlotTimeContributionEffect
)
from bluebottle.time_based.messages import (
    DeadlineChanged,
    ActivitySucceededNotification, ActivitySucceededManuallyNotification,
    ActivityExpiredNotification, ActivityRejectedNotification,
    ActivityCancelledNotification,
    ParticipantAddedNotification, ParticipantCreatedNotification,
    ParticipantAcceptedNotification, ParticipantRejectedNotification,
    ParticipantRemovedNotification, NewParticipantNotification, SlotDateChanged
)
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, TimeContribution, DateActivitySlot, PeriodActivitySlot, SlotParticipant
)
from bluebottle.time_based.states import (
    TimeBasedStateMachine, DateStateMachine, PeriodStateMachine, ActivitySlotStateMachine,
    ParticipantStateMachine, TimeContributionStateMachine, SlotParticipantStateMachine
)


def is_full(effect):
    """
    the activity is full
    """
    return (
        effect.instance.capacity and
        effect.instance.capacity <= len(effect.instance.accepted_participants)
    )


def is_not_full(effect):
    """
    the activity is not full
    """
    return (
        effect.instance.capacity and
        effect.instance.capacity > len(effect.instance.accepted_participants)
    )


def has_participants(effect):
    """ has participants"""
    return len(effect.instance.active_participants) > 0


def has_accepted_participants(effect):
    """ has accepted participants"""
    return len(effect.instance.accepted_participants) > 0


def has_no_participants(effect):
    """
    has no participants
    """
    return len(effect.instance.active_participants) == 0


def is_finished(effect):
    """
    is finished
    """
    return (
        effect.instance.start and
        effect.instance.duration and
        effect.instance.start + effect.instance.duration < now()
    )


def is_not_finished(effect):
    """
    is not finished
    """
    return (
        effect.instance.start and
        effect.instance.duration and
        effect.instance.start + effect.instance.duration > now()
    )


def registration_deadline_is_passed(effect):
    """
    registration deadline has passed
    """
    return (
        effect.instance.registration_deadline and
        effect.instance.registration_deadline < date.today()
    )


def registration_deadline_is_not_passed(effect):
    """
    registration deadline hasn't passed
    """
    return (
        effect.instance.registration_deadline and
        effect.instance.registration_deadline > date.today()
    )


def deadline_is_passed(effect):
    """
    deadline has passed
    """
    return (
        effect.instance.deadline and
        effect.instance.deadline < date.today()
    )


def deadline_is_not_passed(effect):
    """
    deadline hasn't passed
    """
    return (
        effect.instance.deadline and
        effect.instance.deadline > date.today()
    )


def start_is_not_passed(effect):
    """
    start date hasn't passed
    """
    return (
        effect.instance.start and
        effect.instance.start > date.today()
    )


def is_started(effect):
    """
    has started
    """
    to_compare = now()

    if not isinstance(effect.instance, DateActivity):
        to_compare = to_compare.date()

    return (
        effect.instance.start and
        effect.instance.start < to_compare
    )


def is_not_started(effect):
    """
    hasn't started yet
    """
    to_compare = now()

    if not isinstance(effect.instance, DateActivity):
        to_compare = to_compare.date()

    return (
        effect.instance.start and
        effect.instance.start > to_compare
    )


class TimeBasedTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [
        ModelChangedTrigger(
            'capacity',
            effects=[
                TransitionEffect(TimeBasedStateMachine.reopen, conditions=[
                    is_not_full,
                    registration_deadline_is_not_passed
                ]),
                TransitionEffect(TimeBasedStateMachine.lock, conditions=[
                    is_full,
                    registration_deadline_is_not_passed
                ]),
            ]
        ),

        ModelChangedTrigger(
            'registration_deadline',
            effects=[
                TransitionEffect(TimeBasedStateMachine.lock, conditions=[
                    is_not_full,
                    is_not_started,
                    registration_deadline_is_passed
                ]),
                TransitionEffect(TimeBasedStateMachine.reopen, conditions=[
                    is_full,
                    is_not_started,
                    registration_deadline_is_not_passed
                ]),
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.succeed,
            effects=[
                NotificationEffect(ActivitySucceededNotification),
                ActiveDurationsTransitionEffect(TimeContributionStateMachine.succeed)
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.reject,
            effects=[
                NotificationEffect(ActivityRejectedNotification),
                ActiveDurationsTransitionEffect(TimeContributionStateMachine.fail)
            ]
        ),
        TransitionTrigger(
            TimeBasedStateMachine.cancel,
            effects=[
                NotificationEffect(ActivityCancelledNotification),
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                ActiveDurationsTransitionEffect(TimeContributionStateMachine.fail)
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.restore,
            effects=[
                ActiveDurationsTransitionEffect(TimeContributionStateMachine.reset)
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.expire,
            effects=[
                NotificationEffect(ActivityExpiredNotification),
            ]
        ),
    ]


@register(DateActivity)
class DateActivityTriggers(TimeBasedTriggers):
    triggers = TimeBasedTriggers.triggers + [

        TransitionTrigger(
            DateStateMachine.reopen_manually,
            effects=[
                ClearStartEffect,
                ActiveDurationsTransitionEffect(TimeContributionStateMachine.reset)
            ]
        ),

        TransitionTrigger(
            DateStateMachine.auto_approve,
            effects=[
                TransitionEffect(
                    DateStateMachine.succeed,
                    conditions=[
                        is_finished, has_participants
                    ]
                ),
                TransitionEffect(
                    DateStateMachine.expire,
                    conditions=[
                        is_finished, has_no_participants
                    ]
                ),
            ]
        ),
    ]


def slot_is_complete(effect):
    """
    slot details are complete
    """
    return effect.instance.is_complete


def slot_is_incomplete(effect):
    """
    slot details are not complete
    """
    return not effect.instance.is_complete


def slot_is_started(effect):
    """
    slot start date/time has passed
    """
    return effect.instance.is_complete and effect.instance.start and effect.instance.start < now()


def slot_is_not_started(effect):
    """
    slot start date/time has not passed
    """
    return not slot_is_started(effect)


def slot_is_finished(effect):
    """
    slot end date/time has passed
    """
    return effect.instance.is_complete and effect.instance.end and effect.instance.end < now()


def slot_is_not_finished(effect):
    """
    slot end date/time has not passed
    """
    return not slot_is_finished(effect)


def slot_is_full(effect):
    """
    Slot is full. Capacity is filled by participants.
    """
    participant_count = effect.instance.slot_participants.filter(participant__status='accepted').count()
    if effect.instance.capacity \
            and participant_count >= effect.instance.capacity:
        return True
    return False


def slot_is_not_full(effect):
    """
    slot is not full. Still some spots avaialable
    """
    return not slot_is_full(effect)


def participant_slot_will_be_full(effect):
    """
    the slot will be filled
    """
    if not effect.instance.id:
        return False
    participant_count = effect.instance.slot.slot_participants.filter(participant__status='accepted').count()
    if effect.instance.slot.capacity \
            and participant_count + 1 >= effect.instance.slot.capacity:
        return True
    return False


def participant_slot_will_be_not_full(effect):
    """
    the slot will be unfilled
    """
    participant_count = effect.instance.slot.slot_participants.filter(participant__status='accepted').count()
    if effect.instance.slot.capacity \
            and participant_count - 1 < effect.instance.slot.capacity:
        return True
    return False


class ActivitySlotTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            ActivitySlotStateMachine.initiate,
            effects=[
                CreateSlotParticipantsForSlotsEffect
            ]
        ),
        TransitionTrigger(
            ActivitySlotStateMachine.finish,
            effects=[
                ActiveDurationsTransitionEffect(TimeContributionStateMachine.succeed)
            ]
        ),
        TransitionTrigger(
            ActivitySlotStateMachine.cancel,
            effects=[
                ActiveDurationsTransitionEffect(TimeContributionStateMachine.fail)
            ]
        ),
        TransitionTrigger(
            ActivitySlotStateMachine.reopen,
            effects=[
                ActiveDurationsTransitionEffect(TimeContributionStateMachine.reset)
            ]
        ),
        TransitionTrigger(
            ActivitySlotStateMachine.reschedule,
            effects=[
                ActiveDurationsTransitionEffect(TimeContributionStateMachine.reset)
            ]
        ),
        ModelChangedTrigger(
            ['start', 'duration', 'is_online', 'location'],
            effects=[
                TransitionEffect(
                    ActivitySlotStateMachine.mark_complete,
                    conditions=[slot_is_complete]
                ),
                TransitionEffect(
                    ActivitySlotStateMachine.mark_incomplete,
                    conditions=[slot_is_incomplete]
                ),
            ]
        ),
        ModelChangedTrigger(
            'start',
            effects=[
                TransitionEffect(
                    ActivitySlotStateMachine.start,
                    conditions=[slot_is_started, slot_is_not_finished]
                ),

                TransitionEffect(
                    ActivitySlotStateMachine.finish,
                    conditions=[slot_is_finished]
                ),

                TransitionEffect(
                    ActivitySlotStateMachine.reschedule,
                    conditions=[slot_is_not_started]
                ),
            ]
        ),

        ModelChangedTrigger(
            'capacity',
            effects=[
                TransitionEffect(
                    ActivitySlotStateMachine.lock,
                    conditions=[slot_is_full]
                ),

                TransitionEffect(
                    ActivitySlotStateMachine.unlock,
                    conditions=[slot_is_not_full]
                ),
            ]
        ),

        TransitionTrigger(
            ActivitySlotStateMachine.reschedule,
            effects=[
                TransitionEffect(
                    ActivitySlotStateMachine.lock,
                    conditions=[slot_is_full]
                ),
            ]
        ),

    ]


def all_slots_finished(effect):
    """
    all slots have finished
    """
    return effect.instance.activity.slots.exclude(
        status__in=['finished', 'cancelled', 'deleted']
    ).exclude(
        id=effect.instance.id
    ).count() == 0


def all_slots_cancelled(effect):
    """
    all slots are cancelled
    """
    return effect.instance.activity.slots.exclude(status__in=['cancelled', 'deleted']).count() == 0


def activity_has_no_accepted_participants(effect):
    """
    activity does not have any accepted participants
    """
    return effect.instance.activity.accepted_participants.count() == 0


@register(DateActivitySlot)
class DateActivitySlotTriggers(ActivitySlotTriggers):
    triggers = ActivitySlotTriggers.triggers + [
        TransitionTrigger(
            ActivitySlotStateMachine.reschedule,
            effects=[
                TransitionEffect(ActivitySlotStateMachine.lock, conditions=[is_full]),
            ]
        ),
        TransitionTrigger(
            ActivitySlotStateMachine.finish,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.succeed,
                    conditions=[
                        all_slots_finished,
                        has_accepted_participants
                    ]
                ),
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.expire,
                    conditions=[
                        all_slots_finished,
                        activity_has_no_accepted_participants
                    ]
                ),
                ActiveDurationsTransitionEffect(TimeContributionStateMachine.succeed)
            ]
        ),
        TransitionTrigger(
            ActivitySlotStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.cancel,
                    conditions=[
                        all_slots_cancelled
                    ]
                ),
                ActiveDurationsTransitionEffect(TimeContributionStateMachine.fail)
            ]
        ),
        ModelChangedTrigger(
            'start',
            effects=[
                NotificationEffect(
                    SlotDateChanged,
                    conditions=[
                        is_not_finished
                    ]
                ),
                TransitionEffect(
                    ActivitySlotStateMachine.finish,
                    conditions=[
                        is_finished
                    ]
                ),
                TransitionEffect(
                    ActivitySlotStateMachine.reschedule,
                    conditions=[
                        is_not_finished
                    ]
                ),
                RescheduleDurationsEffect
            ]
        ),

    ]


@register(PeriodActivity)
class PeriodActivityTriggers(TimeBasedTriggers):
    triggers = TimeBasedTriggers.triggers + [
        TransitionTrigger(
            PeriodStateMachine.reschedule,
            effects=[
                TransitionEffect(
                    TimeBasedStateMachine.lock,
                    conditions=[
                        is_full,
                        is_not_started
                    ]
                ),
                TransitionEffect(
                    TimeBasedStateMachine.lock,
                    conditions=[
                        registration_deadline_is_passed,
                        is_not_started
                    ]
                )
            ]
        ),

        TransitionTrigger(
            DateStateMachine.reopen_manually,
            effects=[
                ClearDeadlineEffect,
            ]
        ),

        TransitionTrigger(
            PeriodStateMachine.succeed_manually,
            effects=[
                SetEndDateEffect,
                ActiveDurationsTransitionEffect(TimeContributionStateMachine.succeed),
                NotificationEffect(ActivitySucceededManuallyNotification),
            ]
        ),

        ModelChangedTrigger(
            'start',
            effects=[
                NotificationEffect(
                    DeadlineChanged,
                    conditions=[start_is_not_passed]
                ),
                TransitionEffect(
                    PeriodStateMachine.start,
                    conditions=[is_started]
                ),
                TransitionEffect(
                    PeriodStateMachine.reopen,
                    conditions=[
                        is_not_full,
                        is_not_started
                    ]
                ),
                TransitionEffect(
                    PeriodStateMachine.lock,
                    conditions=[
                        is_full,
                        is_not_started
                    ]
                ),
            ]
        ),
        ModelChangedTrigger(
            'deadline',
            effects=[
                NotificationEffect(
                    DeadlineChanged,
                    conditions=[
                        deadline_is_not_passed
                    ]
                ),
                TransitionEffect(
                    DateStateMachine.succeed,
                    conditions=[
                        deadline_is_passed, has_participants
                    ]
                ),
                TransitionEffect(
                    DateStateMachine.expire,
                    conditions=[
                        deadline_is_passed, has_no_participants
                    ]
                ),
                TransitionEffect(
                    PeriodStateMachine.reschedule,
                    conditions=[
                        deadline_is_not_passed
                    ]
                ),
            ]
        )
    ]


@ register(PeriodActivitySlot)
class PeriodActivitySlotTriggers(ActivitySlotTriggers):
    triggers = ActivitySlotTriggers.triggers + []


def automatically_accept(effect):
    """
    automatically accept participants
    """
    return not effect.instance.activity.review


def needs_review(effect):
    """
    needs review
    """
    return effect.instance.activity.review


def is_not_user(effect):
    """
    User is not the participant
    """
    if 'user' in effect.options:
        return effect.instance.user != effect.options['user']
    return False


def is_user(effect):
    """
    User is the participant
    """
    if 'user' in effect.options:
        return effect.instance.user == effect.options['user']
    return True


def activity_will_be_full(effect):
    """
    the activity is full
    """
    activity = effect.instance.activity
    return (
        activity.capacity and
        activity.capacity == len(activity.accepted_participants) + 1
    )


def activity_will_not_be_full(effect):
    """
    the activity is full
    """
    activity = effect.instance.activity
    return (
        activity.capacity and
        activity.capacity >= len(activity.accepted_participants)
    )


def activity_is_finished(effect):
    """
    the activity has finished
    """
    activity = effect.instance.activity

    if isinstance(activity, DateActivity):
        return (
            activity.start and
            activity.duration and
            activity.start + activity.duration < now()
        )
    elif isinstance(activity, PeriodActivity):
        return (
            activity.deadline and
            activity.deadline < date.today()
        )
    else:
        return False


def slot_selection_is_all(effect):
    """
    all slots ar selected when participant applies
    """
    activity = effect.instance.activity
    return activity.slot_selection == 'all'


class ParticipantTriggers(ContributorTriggers):
    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                NotificationEffect(
                    ParticipantCreatedNotification,
                    conditions=[
                        needs_review,
                        is_user
                    ]
                ),
                TransitionEffect(
                    ParticipantStateMachine.add,
                    conditions=[is_not_user]
                ),
                TransitionEffect(
                    ParticipantStateMachine.accept,
                    conditions=[
                        automatically_accept,
                        is_user
                    ]
                ),
                FollowActivityEffect
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.reapply,
            effects=[
                TransitionEffect(
                    ParticipantStateMachine.accept,
                    conditions=[automatically_accept]
                ),

                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.reset,
                ),
                FollowActivityEffect
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.add,
            effects=[
                NotificationEffect(
                    ParticipantAddedNotification
                ),
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.lock,
                    conditions=[activity_will_be_full]
                ),

                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.succeed,
                    conditions=[activity_is_finished]
                ),

                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.reset,
                ),

                RelatedTransitionEffect(
                    'finished_contributions',
                    TimeContributionStateMachine.succeed,
                ),
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.accept,
            effects=[
                NotificationEffect(
                    NewParticipantNotification,
                    conditions=[automatically_accept]
                ),
                NotificationEffect(
                    ParticipantAcceptedNotification,
                    conditions=[needs_review]
                ),
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.lock,
                    conditions=[activity_will_be_full]
                ),

                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.succeed,
                    conditions=[activity_is_finished]
                ),

                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.reset,
                ),

                RelatedTransitionEffect(
                    'finished_contributions',
                    TimeContributionStateMachine.succeed,
                ),
                FollowActivityEffect
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.reject,
            effects=[
                NotificationEffect(
                    ParticipantRejectedNotification
                ),
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.reopen,
                    conditions=[activity_will_not_be_full]
                ),

                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
                ),
                UnFollowActivityEffect
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.remove,
            effects=[
                NotificationEffect(
                    ParticipantRemovedNotification
                ),
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.reopen,
                    conditions=[activity_will_not_be_full]
                ),

                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
                ),
                UnFollowActivityEffect

            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.reopen,
                    conditions=[activity_will_not_be_full]
                ),

                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
                ),
                UnFollowActivityEffect
            ]
        ),
    ]


@register(DateParticipant)
class DateParticipantTriggers(ParticipantTriggers):
    triggers = ParticipantTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                CreateSlotParticipantsForParticipantsEffect
            ]
        ),
    ]


def participant_slot_is_finished(effect):
    """
    Slot end date/time has passed
    """
    if effect.instance.id:
        return effect.instance.slot.is_complete and effect.instance.slot.end < now()


def participant_will_not_be_attending(effect):
    """
    no more slot participations remaining for this activity (participant unregistered from all slots)
    """
    return len(effect.instance.participant.slot_participants.filter(status='registered')) <= 1


@register(SlotParticipant)
class SlotParticipantTriggers(TriggerManager):

    triggers = [
        TransitionTrigger(
            SlotParticipantStateMachine.initiate,
            effects=[
                CreateSlotTimeContributionEffect,
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.succeed,
                    conditions=[participant_slot_is_finished]
                ),
                RelatedTransitionEffect(
                    'slot',
                    ActivitySlotStateMachine.lock,
                    conditions=[participant_slot_will_be_full]
                ),
            ]
        ),

        TransitionTrigger(
            SlotParticipantStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    'slot',
                    ActivitySlotStateMachine.unlock,
                    conditions=[participant_slot_will_be_not_full]
                ),
                RelatedTransitionEffect(
                    'participant',
                    ParticipantStateMachine.remove,
                    conditions=[participant_will_not_be_attending]
                ),
            ]
        ),

        TransitionTrigger(
            SlotParticipantStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.succeed,
                    conditions=[participant_slot_is_finished]
                ),
                RelatedTransitionEffect(
                    'slot',
                    ActivitySlotStateMachine.lock,
                    conditions=[participant_slot_will_be_full]
                ),
                RelatedTransitionEffect(
                    'participant',
                    ParticipantStateMachine.accept,
                ),
            ]
        ),

        TransitionTrigger(
            SlotParticipantStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    'slot',
                    ActivitySlotStateMachine.unlock,
                    conditions=[participant_slot_will_be_not_full]
                ),
                RelatedTransitionEffect(
                    'participant',
                    ParticipantStateMachine.withdraw,
                    conditions=[participant_will_not_be_attending]
                ),
            ]
        ),

        TransitionTrigger(
            SlotParticipantStateMachine.reapply,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    'slot',
                    ActivitySlotStateMachine.lock,
                    conditions=[participant_slot_will_be_full]
                ),
                RelatedTransitionEffect(
                    'participant',
                    ParticipantStateMachine.reapply,
                ),
            ]
        ),
    ]


@register(PeriodParticipant)
class PeriodParticipantTriggers(ParticipantTriggers):
    triggers = ParticipantTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                CreatePeriodParticipationEffect,
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    'finished_contributions',
                    TimeContributionStateMachine.succeed
                )
            ]
        ),

    ]


def duration_is_finished(effect):
    """
    contribution (slot) has finished
    """
    return (
        (effect.instance.end is None or effect.instance.end < now()) and
        effect.instance.contributor.status in ('accepted', 'new') and
        effect.instance.contributor.activity.status in ('open', 'succeeded')
    )


@register(TimeContribution)
class TimeContributionTriggers(ContributionTriggers):
    triggers = ContributionTriggers.triggers + [
        TransitionTrigger(
            TimeContributionStateMachine.reset,
            effects=[
                TransitionEffect(TimeContributionStateMachine.succeed, conditions=[duration_is_finished]),
            ]
        ),

        TransitionTrigger(
            TimeContributionStateMachine.initiate,
            effects=[
                TransitionEffect(TimeContributionStateMachine.succeed, conditions=[duration_is_finished]),
            ]
        ),
    ]
