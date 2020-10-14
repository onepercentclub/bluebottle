from datetime import timedelta
from django.utils.timezone import now

from bluebottle.fsm.triggers import register, ModelChangedTrigger
from bluebottle.fsm.effects import TransitionEffect
from bluebottle.notifications.effects import NotificationEffect

from bluebottle.activities.triggers import ActivityTriggers

from bluebottle.time_based.models import OnADateActivity, WithADeadlineActivity, OngoingActivity
from bluebottle.time_based.messages import DateChanged
from bluebottle.time_based.states import TimeBasedStateMachine, OnADateStateMachine


def is_full(effect):
    "the activity is full"
    return effect.instance.capacity == len(effect.instance.participants)


def is_not_full(effect):
    "the activity is not full"
    return effect.instance.capacity > len(effect.instance.participants)


def is_finished(effect):
    return (
        effect.instance.start and
        effect.instance.duration and
        effect.instance.start + timedelta(hours=effect.instance.duration) > now()
    )


def is_not_finished(effect):
    return (
        effect.instance.start and
        effect.instance.duration and
        effect.instance.start + timedelta(hours=effect.instance.duration) < now()
    )


def is_running(effect):
    return (
        effect.instance.start and
        effect.instance.duration and
        effect.instance.start > now() and
        effect.instance.start + timedelta(hours=effect.instance.duration) < now()
    )


class TimeBasedTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [
        ModelChangedTrigger(
            'capacity',
            effects=[
                TransitionEffect(TimeBasedStateMachine.reopen, conditions=[
                    is_not_full
                ]),
                TransitionEffect(TimeBasedStateMachine.lock, conditions=[
                    is_full
                ]),
            ]
        ),
    ]


@register(OnADateActivity)
class OnADateTriggers(TimeBasedTriggers):
    triggers = TimeBasedTriggers.triggers + [
        ModelChangedTrigger(
            'start',
            effects=[
                NotificationEffect(
                    DateChanged,
                    conditions=[
                        is_not_finished
                    ]
                ),
                TransitionEffect(
                    OnADateStateMachine.succeed,
                    conditions=[
                        is_finished
                    ]
                ),
                TransitionEffect(
                    OnADateStateMachine.start,
                    conditions=[
                        is_running,
                    ]
                ),
                TransitionEffect(
                    OnADateStateMachine.expire,
                    conditions=[
                        is_finished
                    ]
                ),
                TransitionEffect(
                    OnADateStateMachine.reschedule,
                    conditions=[
                        is_not_finished
                    ]
                ),
            ]
        )
    ]


@register(WithADeadlineActivity)
class WithADeadlineTriggers(TimeBasedTriggers):
    pass


@register(OngoingActivity)
class OngoingTriggers(TimeBasedTriggers):
    pass
