from bluebottle.fsm.effects import RelatedTransitionEffect
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
from bluebottle.time_based.states.participants import ParticipantStateMachine
from bluebottle.time_based.states.slots import TeamScheduleSlotStateMachine
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
                CreateTeamSlotEffect,
                CreateCaptainTeamMemberEffect,
                CreateTeamRegistrationEffect,
            ]
        ),
        TransitionTrigger(
            TeamStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    'slots',
                    TeamScheduleSlotStateMachine.cancel,
                ),
                RelatedTransitionEffect(
                    'team_members',
                    TeamMemberStateMachine.cancel,
                )
            ]
        ),
        TransitionTrigger(
            TeamStateMachine.restore,
            effects=[
                RelatedTransitionEffect(
                    'slots',
                    TeamScheduleSlotStateMachine.restore,
                ),
                RelatedTransitionEffect(
                    'team_members',
                    TeamMemberStateMachine.restore,
                )
            ]
        ),
        TransitionTrigger(
            TeamStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    'slots',
                    TeamScheduleSlotStateMachine.cancel,
                ),
                RelatedTransitionEffect(
                    'team_members',
                    TeamMemberStateMachine.cancel,
                )
            ]
        ),
        TransitionTrigger(
            TeamStateMachine.rejoin,
            effects=[
                RelatedTransitionEffect(
                    'slots',
                    TeamScheduleSlotStateMachine.restore,
                ),
                RelatedTransitionEffect(
                    'team_members',
                    TeamMemberStateMachine.restore,
                )
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
        TransitionTrigger(
            TeamMemberStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    ParticipantStateMachine.withdraw,
                )
            ]
        ),
        TransitionTrigger(
            TeamMemberStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    ParticipantStateMachine.cancel,
                )
            ]
        ),
        TransitionTrigger(
            TeamMemberStateMachine.restore,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    ParticipantStateMachine.restore,
                )
            ]
        ),
        ModelDeletedTrigger(
            effects=[
                DeleteTeamMemberSlotParticipantsEffect,
            ]
        ),
    ]
