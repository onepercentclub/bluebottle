from bluebottle.fsm.triggers import (
    register,
    TransitionTrigger,
    TriggerManager,
)
from bluebottle.time_based.effects.teams import CreateTeamRegistrationEffect, CreateCaptainTeamMemberEffect
from bluebottle.time_based.models import Team
from bluebottle.time_based.states.teams import (
    TeamStateMachine
)


@register(Team)
class TeamTriggers(TriggerManager):

    triggers = [
        TransitionTrigger(
            TeamStateMachine.initiate,
            effects=[
                CreateTeamRegistrationEffect,
                CreateCaptainTeamMemberEffect
            ]
        ),
    ]
