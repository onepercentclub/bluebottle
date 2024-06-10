from bluebottle.fsm.effects import TransitionEffect

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
    def should_auto_accept(effect):
        return effect.instance.activity.review == False

    triggers = [
        TransitionTrigger(
            TeamStateMachine.initiate,
            effects=[
                CreateTeamSlotEffect,
                CreateCaptainTeamMemberEffect,
                CreateTeamRegistrationEffect,
                TransitionEffect(
                    TeamStateMachine.accept, conditions=[should_auto_accept]
                ),
            ],
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
