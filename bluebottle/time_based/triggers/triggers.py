from datetime import date

from django.utils.timezone import now

from bluebottle.activities.messages import (
    ParticipantWithdrewConfirmationNotification,
)
from bluebottle.activities.triggers import ContributorTriggers
from bluebottle.follow.effects import FollowActivityEffect, UnFollowActivityEffect
from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import (
    ModelChangedTrigger,
    ModelDeletedTrigger,
    TransitionTrigger,
    TriggerManager,
    register,
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects import (
    RescheduleSlotDurationsEffect,
    ActiveTimeContributionsTransitionEffect, CreateSlotParticipantsForSlotsEffect, CreateSlotTimeContributionEffect,
    CreatePreparationTimeContributionEffect,
    LockFilledSlotsEffect, UnlockUnfilledSlotsEffect, CreateSlotParticipantsForParticipantsEffect,
)
from bluebottle.time_based.messages import (
    ChangedMultipleDateNotification,
    ChangedSingleDateNotification,
    ManagerParticipantAddedOwnerNotification,
    ManagerSlotParticipantRegisteredNotification,
    ManagerSlotParticipantWithdrewNotification,
    ParticipantAcceptedNotification,
    ParticipantAddedNotification,
    ParticipantAppliedNotification,
    ParticipantChangedNotification,
    ParticipantCreatedNotification,
    ParticipantRejectedNotification,
    ParticipantRemovedNotification,
    ParticipantRemovedOwnerNotification,
    ParticipantSlotParticipantRegisteredNotification,
    ParticipantWithdrewNotification,
    SlotCancelledNotification,
)
from bluebottle.time_based.models import (
    DateActivity,
    DateActivitySlot,
    DateParticipant,
    SlotParticipant,
)
from bluebottle.time_based.states import (
    ActivitySlotStateMachine,
    DateStateMachine,
    ParticipantStateMachine,
    SlotParticipantStateMachine,
    TimeBasedStateMachine,
    TimeContributionStateMachine,
)


def is_full(effect):
    """
    the activity is full
    """
    if (
        isinstance(effect.instance, DateActivity) and
        effect.instance.slots.count() > 1 and
        effect.instance.slot_selection == 'free'
    ):
        return False

    return (
        effect.instance.capacity and
        effect.instance.capacity <= len(effect.instance.accepted_participants)
    )


def activity_has_status_full(effect):
    """
    the activity has status full
    """
    return effect.instance.activity.status == 'full'


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


def has_open_slots(effect):
    """
    has open slots
    """
    return effect.instance.slots.filter(status='open').exits()


def has_no_open_slots(effect):
    """
    has no open slots
    """
    return not has_open_slots(effect)


def is_finished(effect):
    """
    is finished
    """
    if isinstance(effect.instance, DateActivitySlot):
        slot = effect.instance
    else:
        slot = effect.instance.slots.order_by('start').last()
    return (
        slot and
        slot.start and
        slot.duration and
        slot.start + slot.duration < now()
    )


def is_not_finished(effect):
    """
    is not finished
    """
    if isinstance(effect.instance, DateActivitySlot):
        slot = effect.instance
    else:
        slot = effect.instance.slots.order_by('start').last()
    return (
        slot and
        slot.start and
        slot.duration and
        slot.start + slot.duration > now()
    )


def registration_deadline_is_passed(effect):
    """
    registration deadline has passed
    """
    return (
        effect.instance.registration_deadline and
        effect.instance.registration_deadline < date.today()
    )


def deadline_is_passed(effect):
    """
    deadline has passed
    """
    return (
        effect.instance.deadline and
        effect.instance.deadline < date.today()
    )


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
    participant_count = effect.instance.slot_participants.filter(
        participant__status='accepted',
        status__in=['registered', 'succeeded']
    ).count()
    if effect.instance.capacity and participant_count >= effect.instance.capacity:
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
    participant_count = effect.instance.slot.slot_participants.filter(
        status="registered", participant__status='accepted'
    ).count()
    if (
        effect.instance.slot.capacity and
        effect.instance.participant.status == 'accepted' and
        participant_count + 1 >= effect.instance.slot.capacity
    ):
        return True
    return False


def participant_slot_will_be_not_full(effect):
    """
    the slot will be unfilled
    """
    participant_count = effect.instance.slot.slot_participants.filter(
        status='registered',
        participant__status='accepted'
    ).count()
    if effect.instance.slot.capacity and participant_count - 1 < effect.instance.slot.capacity:
        return True
    return False


class ActivitySlotTriggers(TriggerManager):

    def has_one_slot(effect):
        return effect.instance.activity.active_slots.count() == 1

    def has_multiple_slots(effect):
        return effect.instance.activity.active_slots.count() > 1

    triggers = [
        TransitionTrigger(
            ActivitySlotStateMachine.initiate,
            effects=[
                CreateSlotParticipantsForSlotsEffect,
                TransitionEffect(
                    ActivitySlotStateMachine.mark_complete,
                    conditions=[slot_is_complete]
                ),
                TransitionEffect(
                    ActivitySlotStateMachine.finish,
                    conditions=[slot_is_finished]
                ),
            ]
        ),
        TransitionTrigger(
            ActivitySlotStateMachine.finish,
            effects=[
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.succeed)
            ]
        ),
        TransitionTrigger(
            ActivitySlotStateMachine.cancel,
            effects=[
                NotificationEffect(SlotCancelledNotification),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.fail)
            ]
        ),
        TransitionTrigger(
            ActivitySlotStateMachine.reopen,
            effects=[
                TransitionEffect(
                    ActivitySlotStateMachine.finish,
                    conditions=[slot_is_finished]
                ),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.reset)
            ]
        ),
        TransitionTrigger(
            ActivitySlotStateMachine.reschedule,
            effects=[
                TransitionEffect(
                    ActivitySlotStateMachine.finish,
                    conditions=[slot_is_finished]
                ),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.reset)
            ]
        ),
        ModelChangedTrigger(
            ['start', 'duration', 'is_online', 'location_id', 'location_hint'],
            effects=[
                TransitionEffect(
                    ActivitySlotStateMachine.mark_complete,
                    conditions=[slot_is_complete]
                ),
                TransitionEffect(
                    ActivitySlotStateMachine.mark_incomplete,
                    conditions=[slot_is_incomplete]
                ),
                NotificationEffect(
                    ChangedSingleDateNotification,
                    conditions=[
                        has_accepted_participants,
                        is_not_finished,
                        has_one_slot
                    ]
                ),
                NotificationEffect(
                    ChangedMultipleDateNotification,
                    conditions=[
                        has_accepted_participants,
                        is_not_finished,
                        has_multiple_slots
                    ]
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


def not_all_slots_finished(effect):
    """
    not all slots have finished
    """
    return not all_slots_finished(effect)


def all_slots_cancelled(effect):
    """
    all slots are cancelled
    """
    return effect.instance.activity.slots.exclude(
        status__in=['cancelled', 'deleted']
    ).exclude(
        id=effect.instance.id,
    ).count() == 0


def all_slots_will_be_full(effect):
    """
    no open slots left
    """
    return effect.instance.activity.slots.exclude(id=effect.instance.id).filter(status__in=['open']).count() == 0


def activity_has_no_accepted_participants(effect):
    """
    activity does not have any accepted participants
    """
    return effect.instance.activity.accepted_participants.count() == 0


def activity_has_accepted_participants(effect):
    """
    activity does not have any accepted participants
    """
    return effect.instance.activity.accepted_participants.count() > 0


@register(DateActivitySlot)
class DateActivitySlotTriggers(ActivitySlotTriggers):
    triggers = ActivitySlotTriggers.triggers + [
        TransitionTrigger(
            ActivitySlotStateMachine.mark_complete,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.reopen,
                ),

                RelatedTransitionEffect(
                    'activity',
                    DateStateMachine.reschedule,
                ),
            ]
        ),
        ModelDeletedTrigger(
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.succeed,
                    conditions=[
                        all_slots_finished,
                        activity_has_accepted_participants
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
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.lock,
                    conditions=[
                        not_all_slots_finished,
                        all_slots_will_be_full,
                    ]
                ),
            ]
        ),

        TransitionTrigger(
            ActivitySlotStateMachine.reschedule,
            effects=[
                TransitionEffect(ActivitySlotStateMachine.lock, conditions=[is_full]),

                RelatedTransitionEffect(
                    'activity',
                    DateStateMachine.reschedule,
                ),
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
                        activity_has_accepted_participants
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
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.succeed)
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
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.succeed,
                    conditions=[
                        all_slots_finished,
                        activity_has_accepted_participants
                    ]
                ),
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.lock,
                    conditions=[
                        not_all_slots_finished,
                        all_slots_will_be_full,
                    ]
                ),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.fail)
            ]
        ),
        TransitionTrigger(
            ActivitySlotStateMachine.lock,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.lock,
                    conditions=[
                        all_slots_will_be_full,
                    ]
                ),
            ]
        ),
        TransitionTrigger(
            ActivitySlotStateMachine.unlock,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.unlock,
                    conditions=[
                        activity_has_status_full
                    ]
                ),
            ]
        ),
        ModelChangedTrigger(
            'start',
            effects=[
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
                RescheduleSlotDurationsEffect
            ]
        ),

        ModelChangedTrigger(
            'duration',
            effects=[
                RescheduleSlotDurationsEffect
            ]
        ),

    ]


def is_not_user(effect):
    """
    User is not the participant
    """
    if 'user' in effect.options:
        return effect.instance.user != effect.options['user']
    return True


def is_user(effect):
    """
    User is the participant
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


def activity_will_be_full(effect):
    """
    the activity is full
    """
    activity = effect.instance.activity
    if activity.team_activity == 'teams':
        accepted_teams = activity.teams.filter(status__in=['open', 'running', 'finished']).count()
        return (
            activity.capacity and
            activity.capacity <= accepted_teams
        )

    if isinstance(activity, DateActivity) and activity.slot_selection == 'free':
        # Don't trigger 'full' effects on DateActivity, slots will trigger them
        return False

    return (
        activity.capacity and
        activity.capacity == len(activity.accepted_participants) + 1
    )


def activity_will_not_be_full(effect):
    """
    the activity is full
    """
    activity = effect.instance.activity
    if isinstance(activity, DateActivity) and activity.slot_selection == 'free':
        # Don't trigger 'full' effects on DateActivity, slots will trigger them
        return False
    if activity.team_activity == 'teams':
        accepted_teams = activity.teams.filter(status__in=['open', 'running', 'finished']).count()
        return (
            not activity.capacity or
            activity.capacity > accepted_teams
        )
    return (
        not activity.capacity or
        activity.capacity >= len(activity.accepted_participants)
    )


def activity_is_finished(effect):
    """
    the activity has finished
    """
    activity = effect.instance.activity

    last_slot = activity.slots.order_by('start').last()
    return (
        last_slot and
        last_slot.start and
        last_slot.duration and
        last_slot.start + last_slot.duration < now()
    )


class ParticipantTriggers(ContributorTriggers):
    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                NotificationEffect(
                    ParticipantAppliedNotification,
                    conditions=[
                        needs_review,
                        is_user
                    ]
                ),
                NotificationEffect(
                    ParticipantCreatedNotification,
                    conditions=[
                        needs_review,
                        is_user
                    ]
                ),
                TransitionEffect(
                    ParticipantStateMachine.add,
                    conditions=[
                        is_not_user
                    ]
                ),
                TransitionEffect(
                    ParticipantStateMachine.accept,
                    conditions=[
                        automatically_accept,
                        is_user
                    ]
                ),
                FollowActivityEffect,
                CreatePreparationTimeContributionEffect,
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.reapply,
            effects=[
                NotificationEffect(
                    ParticipantAppliedNotification,
                    conditions=[
                        needs_review,
                        is_user,
                    ]
                ),
                NotificationEffect(
                    ParticipantCreatedNotification,
                    conditions=[
                        needs_review,
                        is_user
                    ]
                ),
                TransitionEffect(
                    ParticipantStateMachine.accept,
                    conditions=[
                        automatically_accept
                    ]
                ),
                FollowActivityEffect,
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.add,
            effects=[
                NotificationEffect(
                    ParticipantAddedNotification,
                ),
                NotificationEffect(
                    ManagerParticipantAddedOwnerNotification
                ),
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.lock,
                    conditions=[
                        activity_will_be_full
                    ]
                ),
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.succeed,
                    conditions=[activity_is_finished]
                ),

                RelatedTransitionEffect(
                    'upcoming_contributions',
                    TimeContributionStateMachine.reset,
                ),
                RelatedTransitionEffect(
                    'finished_contributions',
                    TimeContributionStateMachine.succeed,
                ),
                RelatedTransitionEffect(
                    'started_contributions',
                    TimeContributionStateMachine.succeed,
                ),
                RelatedTransitionEffect(
                    'preparation_contributions',
                    TimeContributionStateMachine.succeed,
                ),
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.accept,
            effects=[
                NotificationEffect(
                    ParticipantAcceptedNotification,
                    conditions=[
                        needs_review,
                    ]
                ),
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.lock,
                    conditions=[
                        activity_will_be_full
                    ]
                ),
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.succeed,
                    conditions=[activity_is_finished]
                ),
                RelatedTransitionEffect(
                    'preparation_contributions',
                    TimeContributionStateMachine.succeed,
                ),
                FollowActivityEffect,
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.reject,
            effects=[
                NotificationEffect(
                    ParticipantRejectedNotification,
                ),

                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.unlock,
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
                NotificationEffect(
                    ParticipantRemovedOwnerNotification,
                    conditions=[
                        is_not_owner,
                    ]
                ),
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.unlock,
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
                    TimeBasedStateMachine.unlock,
                    conditions=[activity_will_not_be_full]
                ),
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
                ),
                UnFollowActivityEffect,
                NotificationEffect(
                    ParticipantWithdrewNotification,
                ),
                NotificationEffect(
                    ParticipantWithdrewConfirmationNotification
                ),
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
        TransitionTrigger(
            ParticipantStateMachine.accept,
            effects=[
                LockFilledSlotsEffect,
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.reset,
                ),
            ]
        ),
        TransitionTrigger(
            ParticipantStateMachine.reject,
            effects=[
                UnlockUnfilledSlotsEffect,
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.remove,
            effects=[
                UnlockUnfilledSlotsEffect,
            ]
        ),
    ]


def participant_slot_is_finished(effect):
    """
    Slot end date/time has passed
    """
    if effect.instance.id:
        return effect.instance.slot.is_complete and effect.instance.slot.end < now()


def applicant_is_accepted(effect):
    return effect.instance.participant.status == 'accepted'


def is_participant(effect):
    if 'user' not in effect.options:
        return False
    return effect.instance.participant.user == effect.options['user']


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
                NotificationEffect(
                    ManagerSlotParticipantRegisteredNotification,
                    conditions=[
                        applicant_is_accepted,
                        is_participant
                    ]
                ),
                NotificationEffect(
                    ParticipantSlotParticipantRegisteredNotification,
                    conditions=[
                        applicant_is_accepted,
                        is_participant
                    ]
                )
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
                NotificationEffect(ParticipantChangedNotification),
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
                NotificationEffect(ParticipantChangedNotification),
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
                NotificationEffect(
                    ManagerSlotParticipantWithdrewNotification,
                ),
            ]
        ),

        TransitionTrigger(
            SlotParticipantStateMachine.reapply,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.reset,
                ),
                RelatedTransitionEffect(
                    'slot',
                    ActivitySlotStateMachine.lock,
                    conditions=[participant_slot_will_be_full]
                ),
                RelatedTransitionEffect(
                    'slot',
                    ActivitySlotStateMachine.lock,
                    conditions=[participant_slot_will_be_full]
                ),
                NotificationEffect(ParticipantChangedNotification),
                NotificationEffect(
                    ManagerSlotParticipantRegisteredNotification,
                    conditions=[applicant_is_accepted]
                )

            ]
        ),
    ]
