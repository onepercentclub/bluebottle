from bluebottle.activities.states import ContributionStateMachine
from bluebottle.activities.triggers import (
    ContributorTriggers
)
from bluebottle.follow.effects import FollowActivityEffect
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    TransitionTrigger, register
)
from bluebottle.time_based.effects import CreatePreparationTimeContributionEffect
from bluebottle.time_based.effects.participant import CreateTimeContributionEffect
from bluebottle.time_based.models import DeadlineParticipant
from bluebottle.time_based.states import (
    ParticipantStateMachine, DeadlineParticipantStateMachine
)


@register(DeadlineParticipant)
class DeadlineParticipantTriggers(ContributorTriggers):
    def review_needed(effect):
        return effect.instance.activity.review

    def no_review_needed(effect):
        return not effect.instance.activity.review

    triggers = [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                FollowActivityEffect,
                CreatePreparationTimeContributionEffect,
                CreateTimeContributionEffect,
                TransitionEffect(
                    ParticipantStateMachine.accept,
                    conditions=[
                        no_review_needed
                    ]
                ),
            ]
        ),
        TransitionTrigger(
            ParticipantStateMachine.accept,
            effects=[
                TransitionEffect(
                    DeadlineParticipantStateMachine.succeed,
                ),
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    ContributionStateMachine.succeed,
                ),
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    ContributionStateMachine.fail,
                ),
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    ContributionStateMachine.fail,
                ),
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.cancelled,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    ContributionStateMachine.fail,
                ),
            ]
        ),
    ]
