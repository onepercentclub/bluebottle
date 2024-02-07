from bluebottle.activities.triggers import (
    ContributorTriggers
)
from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.triggers import (
    TransitionTrigger, register
)
from bluebottle.time_based.models import DeadlineParticipant
from bluebottle.time_based.states import (
    ParticipantStateMachine
)


class ParticipantTriggers(ContributorTriggers):
    def review_needed(effect):
        return effect.instance.activity.review

    def no_review_needed(effect):
        return not effect.instance.activity.review

    triggers = [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                TransitionEffect(
                    ParticipantStateMachine.accept,
                    conditions=[
                        no_review_needed
                    ]
                ),
            ]
        ),
    ]


@register(DeadlineParticipant)
class DeadlineParticipantTriggers(ParticipantTriggers):
    pass
