from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.states import ParticipantStateMachine, PeriodActivitySlotStateMachine


class SlotTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            SlotStateMachine.finish,
            effects=[
                RelatedTransitionEffect('participants', ParticipantStateMachine.succeed)
            ]
        ),
        TransitionTrigger(
            SlotStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('participants', ParticipantStateMachine.cancel)
            ]
        ),
    ]


@register(PredefinedSlot)
class PredefinedSlotTriggers(SlotTriggers):
    triggers = SlotTriggers.triggers + [
        ModelChangedTrigger(
            'capacity',
            effects=[
                TransitionEffect(
                    PredefinedSlotStateMachine.lock,
                    conditions=[slot_is_full]
                ),

                TransitionEffect(
                    PredefinedSlotStateMachine.unlock,
                    conditions=[slot_is_not_full]
                ),
            ]
        ),
        TransitionTrigger(
            PredefinedSlotStateMachine.reschedule,
            effects=[
                TransitionEffect(
                    PredefinedSlotStateMachine.lock,
                    conditions=[slot_is_full]
                ),
            ]
        ),

        ModelChangedTrigger(
            ['start', 'duration', 'is_online', 'location_id', 'location_hint'],
            effects=[
                TransitionEffect(
                    PeriodicSlotStateMachine.mark_complete,
                    conditions=[slot_is_complete]
                ),
                TransitionEffect(
                    PeriodicSlotStateMachine.mark_incomplete,
                    conditions=[slot_is_incomplete]
                ),
                NotificationEffect(
                    PeriodicChangedSlotNotification,
                    conditions=[is_not_finished, ]
                ),
            ]
        ),
        ModelChangedTrigger(
            'start',
            effects=[
                TransitionEffect(
                    SlotStateMachine.start,
                    conditions=[slot_is_started, slot_is_not_finished]
                ),

                TransitionEffect(
                    SlotStateMachine.finish,
                    conditions=[slot_is_finished]
                ),
                TransitionEffect(
                    SlotStateMachine.reschedule,
                    conditions=[slot_is_not_started]
                ),
            ]
        ),

    ]


@register(TBASlot)
class TBASlotTriggers(SlotTriggers):
    triggers = SlotTriggers.triggers + [
        TransitionTrigger(
            TBASlotTriggers.initiate,
            effects=[
                NotificationEffect(
                    TBASlotCreatedNotification,
                ),
            ]
        ),
        TransitionTrigger(
            TBASlotTriggers.mark_complete,
            effects=[
                NotificationEffect(
                    TBASlotCompletedNotification,
                ),
            ]
        ),

        ModelChangedTrigger(
            ['start', 'duration', 'is_online', 'location_id', 'location_hint'],
            effects=[
                NotificationEffect(
                    TBAChangedSlotNotification,
                    conditions=[is_not_finished, is_complete]
                ),
            ]
        ),
        ModelChangedTrigger(
            'start',
            effects=[
                TransitionEffect(
                    TBASlotStateMachine.start,
                    conditions=[is_started, is_not_finished]
                ),

                TransitionEffect(
                    TBASlotStateMachine.finish,
                    conditions=[is_finished]
                ),
                TransitionEffect(
                    TBASlotStateMachine.reschedule,
                    conditions=[is_not_started]
                ),
            ]
        ),
    ]


@register(PeriodicSlot)
class PeriodicSlotTriggers(SlotTriggers):
    triggers = SlotTriggers.triggers + [
        TransitionTrigger(
            PeriodActivitySlotStateMachine.finished,
            effects=[
                CreateNewSlotEffect(),
            ]
        ),
    ]
