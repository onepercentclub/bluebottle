from datetime import date

from django.utils.timezone import now

from bluebottle.activities.messages import (
    ActivitySucceededNotification,
    ActivityExpiredNotification, ActivityRejectedNotification,
    ActivityCancelledNotification, ActivityRestoredNotification,
    ParticipantWithdrewConfirmationNotification,
    TeamMemberAddedMessage, TeamMemberWithdrewMessage, TeamMemberRemovedMessage
)
from bluebottle.activities.states import OrganizerStateMachine, TeamStateMachine
from bluebottle.activities.triggers import (
    ActivityTriggers, ContributorTriggers, ContributionTriggers
)
from bluebottle.activities.effects import CreateTeamEffect, CreateInviteEffect

from bluebottle.follow.effects import (
    FollowActivityEffect, UnFollowActivityEffect
)
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    register, ModelChangedTrigger, ModelDeletedTrigger, TransitionTrigger, TriggerManager
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects import (
    CreatePeriodTimeContributionEffect, CreateOverallTimeContributionEffect, SetEndDateEffect,
    ClearDeadlineEffect,
    RescheduleSlotDurationsEffect,
    ActiveTimeContributionsTransitionEffect, CreateSlotParticipantsForParticipantsEffect,
    CreateSlotParticipantsForSlotsEffect, CreateSlotTimeContributionEffect, UnlockUnfilledSlotsEffect,
    LockFilledSlotsEffect, CreatePreparationTimeContributionEffect,
    ResetSlotSelectionEffect, UnsetCapacityEffect,
    RescheduleOverallPeriodActivityDurationsEffect,
)
from bluebottle.time_based.messages import (
    DeadlineChangedNotification,
    ParticipantAddedNotification, ParticipantCreatedNotification,
    ParticipantAcceptedNotification, ParticipantRejectedNotification,
    ParticipantRemovedNotification, TeamParticipantRemovedNotification, NewParticipantNotification,
    ParticipantFinishedNotification,
    ChangedSingleDateNotification, ChangedMultipleDateNotification,
    ActivitySucceededManuallyNotification, ParticipantChangedNotification,
    ParticipantWithdrewNotification, ParticipantAddedOwnerNotification,
    ParticipantRemovedOwnerNotification, ParticipantJoinedNotification, TeamParticipantJoinedNotification,
    ParticipantAppliedNotification, TeamParticipantAppliedNotification, SlotCancelledNotification
)
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, TimeContribution, DateActivitySlot,
    PeriodActivitySlot, SlotParticipant
)
from bluebottle.time_based.states import (
    TimeBasedStateMachine, DateStateMachine, PeriodStateMachine, ActivitySlotStateMachine,
    ParticipantStateMachine, TimeContributionStateMachine, SlotParticipantStateMachine,
    PeriodParticipantStateMachine
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


def registration_deadline_is_not_passed(effect):
    """
    registration deadline hasn't passed
    """
    return not registration_deadline_is_passed(effect)


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
    return not deadline_is_passed(effect)


def start_is_not_passed(effect):
    """
    start date hasn't passed
    """
    return (
        effect.instance.start is None or
        effect.instance.start > date.today()
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

        TransitionTrigger(
            TimeBasedStateMachine.succeed,
            effects=[
                NotificationEffect(ActivitySucceededNotification),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.succeed)
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.reject,
            effects=[
                NotificationEffect(ActivityRejectedNotification),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.fail)
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.cancel,
            effects=[
                NotificationEffect(ActivityCancelledNotification),
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.fail)
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.restore,
            effects=[
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.reset),
                NotificationEffect(ActivityRestoredNotification)
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
        ModelChangedTrigger(
            'registration_deadline',
            effects=[
                TransitionEffect(TimeBasedStateMachine.lock, conditions=[
                    registration_deadline_is_passed
                ]),
                TransitionEffect(TimeBasedStateMachine.reopen, conditions=[
                    registration_deadline_is_not_passed
                ]),
            ]
        ),

        ModelChangedTrigger(
            'slot_selection',
            effects=[
                UnsetCapacityEffect
            ]
        ),

        TransitionTrigger(
            DateStateMachine.reopen_manually,
            effects=[
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.reset)
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
    participant_count = effect.instance.slot.slot_participants.filter(participant__status='accepted').count()
    if effect.instance.slot.capacity \
            and effect.instance.participant.status == 'accepted' \
            and participant_count + 1 >= effect.instance.slot.capacity:
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
    if effect.instance.slot.capacity \
            and participant_count - 1 < effect.instance.slot.capacity:
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
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.reset)
            ]
        ),
        TransitionTrigger(
            ActivitySlotStateMachine.reschedule,
            effects=[
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


def slot_selection_is_all(effect):
    """
    all slots ar selected when participant applies
    """
    activity = effect.instance.activity
    return activity.slot_selection == 'all'


def slot_selection_is_free(effect):
    """
    all slots ar selected when participant applies
    """
    activity = effect.instance.activity
    return activity.slot_selection == 'free'


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
                ResetSlotSelectionEffect,
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
                        slot_selection_is_free
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
                        slot_selection_is_free
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
                        slot_selection_is_free,
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


@register(PeriodActivity)
class PeriodActivityTriggers(TimeBasedTriggers):
    triggers = TimeBasedTriggers.triggers + [
        ModelChangedTrigger(
            'registration_deadline',
            effects=[
                TransitionEffect(TimeBasedStateMachine.lock, conditions=[
                    registration_deadline_is_passed
                ]),
                TransitionEffect(TimeBasedStateMachine.reopen, conditions=[
                    registration_deadline_is_not_passed
                ]),
            ]
        ),

        ModelChangedTrigger(
            ['start', 'deadline'],
            effects=[
                RescheduleOverallPeriodActivityDurationsEffect
            ]
        ),

        TransitionTrigger(
            PeriodStateMachine.reschedule,
            effects=[
                TransitionEffect(
                    TimeBasedStateMachine.lock,
                    conditions=[
                        is_full,
                    ]
                ),
                TransitionEffect(
                    TimeBasedStateMachine.lock,
                    conditions=[
                        registration_deadline_is_passed,
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
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.succeed),
                NotificationEffect(ActivitySucceededManuallyNotification),
            ]
        ),

        ModelChangedTrigger(
            'start',
            effects=[
                NotificationEffect(
                    DeadlineChangedNotification,
                    conditions=[start_is_not_passed]
                ),
                TransitionEffect(
                    PeriodStateMachine.reopen,
                    conditions=[
                        is_not_full,
                    ]
                ),
                TransitionEffect(
                    PeriodStateMachine.lock,
                    conditions=[
                        is_full,
                    ]
                ),
            ]
        ),
        ModelChangedTrigger(
            'deadline',
            effects=[
                NotificationEffect(
                    DeadlineChangedNotification,
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


def not_team_captain(effect):
    """
    not a team captain
    """
    return not effect.instance.team or effect.instance.team.owner != effect.instance.user


def user_is_not_team_captain(effect):
    """
    current user is not team captain
    """
    return not effect.instance.team or effect.instance.team.owner != effect.options['user']


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


def is_owner(effect):
    """
    User is the owner
    """
    if 'user' in effect.options:
        return effect.instance.activity.owner == effect.options['user']
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

    if (
        isinstance(activity, DateActivity) and
        activity.slots.count() > 1 and
        activity.slot_selection == 'free'
    ):
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
        last_slot = activity.slots.order_by('start').last()
        return (
            last_slot and
            last_slot.start and
            last_slot.duration and
            last_slot.start + last_slot.duration < now()
        )
    elif isinstance(activity, PeriodActivity):
        return (
            activity.deadline and
            activity.deadline < date.today()
        )
    else:
        return False


def team_is_active(effect):
    """Team status is open, or there is no team"""
    return (
        effect.instance.team.status in [TeamStateMachine.open.value, TeamStateMachine.new.value]
        if effect.instance.team
        else True
    )


def team_is_open(effect):
    """Team status is open, or there is no team"""
    return (
        effect.instance.accepted_invite.contributor.team.status == TeamStateMachine.open.value
        if effect.instance.accepted_invite
        else False
    )


def has_accepted_invite(effect):
    """Contribtor is part of a team"""
    return effect.instance.accepted_invite and effect.instance.accepted_invite.contributor.team


def is_team_activity(effect):
    """Contribtor is part of a team"""
    return effect.instance.activity.team_activity == 'teams'


def is_not_team_activity(effect):
    """Contribtor is not part of a team"""
    return not effect.instance.team


def has_team(effect):
    """
    Participant belongs to a team
    """
    return effect.instance.team


class ParticipantTriggers(ContributorTriggers):
    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                CreateTeamEffect,
                NotificationEffect(
                    ParticipantAppliedNotification,
                    conditions=[
                        needs_review,
                        not_team_captain,
                        is_user
                    ]
                ),
                NotificationEffect(
                    TeamParticipantAppliedNotification,
                    conditions=[
                        needs_review,
                        is_team_activity,
                        is_user
                    ]
                ),
                NotificationEffect(
                    ParticipantCreatedNotification,
                    conditions=[
                        needs_review,
                        not_team_captain,
                        is_user
                    ]
                ),
                NotificationEffect(
                    TeamMemberAddedMessage,
                    conditions=[
                        has_accepted_invite
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
                TransitionEffect(
                    ParticipantStateMachine.accept,
                    conditions=[
                        has_accepted_invite,
                        team_is_open
                    ]
                ),
                FollowActivityEffect,
                CreatePreparationTimeContributionEffect,
                CreateInviteEffect
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
                        not_team_captain
                    ]
                ),
                NotificationEffect(
                    TeamParticipantAppliedNotification,
                    conditions=[
                        needs_review,
                        is_user,
                        is_team_activity
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
                TransitionEffect(
                    ParticipantStateMachine.accept,
                    conditions=[
                        has_accepted_invite,
                        team_is_open
                    ]
                ),
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.reset,
                    conditions=[team_is_active]
                ),
                FollowActivityEffect,
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.add,
            effects=[
                NotificationEffect(
                    ParticipantAddedNotification
                ),
                NotificationEffect(
                    ParticipantAddedOwnerNotification
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
                    NewParticipantNotification,
                    conditions=[
                        not_team_captain,
                        automatically_accept
                    ]
                ),
                RelatedTransitionEffect(
                    'team',
                    TeamStateMachine.accept,
                    conditions=[has_team]
                ),
                NotificationEffect(
                    ParticipantJoinedNotification,
                    conditions=[automatically_accept, not_team_captain]
                ),
                NotificationEffect(
                    TeamParticipantJoinedNotification,
                    conditions=[automatically_accept, is_team_activity]
                ),
                NotificationEffect(
                    ParticipantAcceptedNotification,
                    conditions=[
                        needs_review,
                        not_team_captain
                    ]
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
                    conditions=[team_is_active]
                ),
                RelatedTransitionEffect(
                    'finished_contributions',
                    TimeContributionStateMachine.succeed,
                    conditions=[team_is_active]
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
                NotificationEffect(
                    TeamParticipantRemovedNotification,
                    conditions=[has_accepted_invite]
                ),
                NotificationEffect(
                    ParticipantRemovedOwnerNotification,
                    conditions=[
                        is_not_owner,
                        is_not_team_activity
                    ]
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
                NotificationEffect(
                    TeamMemberRemovedMessage,
                    conditions=[
                        user_is_not_team_captain,
                    ]
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
                UnFollowActivityEffect,
                NotificationEffect(ParticipantWithdrewNotification),
                NotificationEffect(ParticipantWithdrewConfirmationNotification),
                NotificationEffect(TeamMemberWithdrewMessage),
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
            ParticipantStateMachine.reapply,
            effects=[
                LockFilledSlotsEffect,
            ]
        ),
        TransitionTrigger(
            ParticipantStateMachine.accept,
            effects=[
                LockFilledSlotsEffect,
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

        TransitionTrigger(
            ParticipantStateMachine.withdraw,
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
                NotificationEffect(ParticipantChangedNotification),
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
                RelatedTransitionEffect(
                    'participant',
                    ParticipantStateMachine.accept,
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
                RelatedTransitionEffect(
                    'participant',
                    ParticipantStateMachine.withdraw,
                    conditions=[participant_will_not_be_attending]
                ),
                NotificationEffect(ParticipantChangedNotification),
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
                    'participant',
                    ParticipantStateMachine.reapply,
                ),
                RelatedTransitionEffect(
                    'slot',
                    ActivitySlotStateMachine.lock,
                    conditions=[participant_slot_will_be_full]
                ),
                NotificationEffect(ParticipantChangedNotification),
            ]
        ),
    ]


@register(PeriodParticipant)
class PeriodParticipantTriggers(ParticipantTriggers):
    triggers = ParticipantTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                CreatePeriodTimeContributionEffect,
                CreateOverallTimeContributionEffect
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    'finished_contributions',
                    TimeContributionStateMachine.succeed
                ),
            ]
        ),

        TransitionTrigger(
            PeriodParticipantStateMachine.stop,
            effects=[
                NotificationEffect(ParticipantFinishedNotification),
            ]
        ),

    ]


def duration_is_finished(effect):
    """
    contribution (slot) has finished
    """
    if effect.instance.contribution_type == 'preparation':
        if effect.instance.contributor.status in ('accepted',):
            return True
        else:
            return False
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
                TransitionEffect(
                    TimeContributionStateMachine.succeed,
                    conditions=[
                        duration_is_finished
                    ]),
            ]
        ),

        TransitionTrigger(
            TimeContributionStateMachine.initiate,
            effects=[
                TransitionEffect(
                    TimeContributionStateMachine.succeed,
                    conditions=[
                        duration_is_finished
                    ]),
            ]
        ),

    ]
