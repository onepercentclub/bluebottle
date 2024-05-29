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
    ]
