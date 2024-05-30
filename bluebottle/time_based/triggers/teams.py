from bluebottle.fsm.triggers import (
    register,
    TransitionTrigger,
    TriggerManager,
    ModelDeletedTrigger
)
from bluebottle.time_based.effects.teams import (
    CreateTeamRegistrationEffect,
    CreateCaptainTeamMemberEffect,
    CreateTeamSlotEffect,
    CreateTeamMemberSlotParticipantsEffect,
    DeleteTeamMemberSlotParticipantsEffect
)
from bluebottle.time_based.models import Team, TeamMember
from bluebottle.time_based.states.teams import (
    TeamStateMachine,
    TeamMemberStateMachine
)


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


@register(TeamMember)
class TeamMemberTriggers(TriggerManager):

    triggers = [
        TransitionTrigger(
            TeamMemberStateMachine.initiate,
            effects=[
                CreateTeamMemberSlotParticipantsEffect,
            ]
        ),
        ModelDeletedTrigger(
            effects=[
                DeleteTeamMemberSlotParticipantsEffect,
            ]
        ),
    ]
