from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    register,
    TransitionTrigger,
    TriggerManager,
)
from bluebottle.time_based.effects.teams import (
    CreateTeamRegistrationEffect,
    CreateCaptainTeamMemberEffect,
    CreateTeamSlotEffect,
)
from bluebottle.time_based.models import Team
from bluebottle.time_based.states.teams import TeamMemberStateMachine, TeamStateMachine


@register(Team)
class TeamTriggers(TriggerManager):

    triggers = [
        TransitionTrigger(
            TeamStateMachine.initiate,
            effects=[
                CreateTeamRegistrationEffect,
                CreateCaptainTeamMemberEffect,
                CreateTeamSlotEffect,
            ]
        ),
        TransitionTrigger(
            TeamStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    "team",
                    TeamMemberStateMachine.accept,
                ),
            ],
        ),
        TransitionTrigger(
            TeamStateMachine.reject,
            effects=[
                RelatedTransitionEffect(
                    "team",
                    TeamMemberStateMachine.reject,
                ),
            ],
        ),
        TransitionTrigger(
            TeamStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    "team",
                    TeamMemberStateMachine.remove,
                ),
            ],
        ),
        TransitionTrigger(
            TeamStateMachine.readd,
            effects=[
                RelatedTransitionEffect(
                    "team",
                    TeamMemberStateMachine.readd,
                ),
            ],
        ),
    ]
