from datetime import date

from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.triggers import (
    ModelChangedTrigger, TransitionTrigger, TriggerManager, register
)
from bluebottle.voting.models import Poll
from bluebottle.voting.states import PollStateMachine


def is_deadline_passed(effect):
    """
    deadline has passed
    """
    return (
        effect.instance.end_date and
        effect.instance.end_date < date.today()
    )


def is_deadline_not_passed(effect):
    """
    deadline has not passed
    """
    return not is_deadline_passed(effect)


def is_closed(effect):
    """
    poll is closed
    """
    return effect.instance.status == 'closed'


@register(Poll)
class PollTriggers(TriggerManager):
    triggers = [
        ModelChangedTrigger(
            'end_date',
            effects=[
                TransitionEffect(
                    PollStateMachine.close,
                    conditions=[is_deadline_passed]
                ),
                TransitionEffect(
                    PollStateMachine.reopen,
                    conditions=[is_deadline_not_passed, is_closed]
                ),
            ]
        ),
        TransitionTrigger(
            PollStateMachine.publish,
            effects=[
                TransitionEffect(
                    PollStateMachine.close,
                    conditions=[is_deadline_passed]
                ),
            ]
        ),
    ]
