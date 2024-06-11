from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect

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
    DeleteTeamMemberSlotParticipantsEffect,
)
from bluebottle.time_based.models import Team, TeamMember
from bluebottle.time_based.states.participants import (
    TeamScheduleParticipantStateMachine,
)
from bluebottle.time_based.states.teams import TeamStateMachine, TeamMemberStateMachine


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
        TransitionTrigger(
            TeamStateMachine.reject,
            effects=[
                RelatedTransitionEffect(
                    "team_members",
                    TeamMemberStateMachine.reject,
                ),
            ],
        ),
        TransitionTrigger(
            TeamStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    "team_members",
                    TeamMemberStateMachine.accept,
                ),
            ],
        ),
        TransitionTrigger(
            TeamStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    "team_members",
                    TeamMemberStateMachine.withdraw,
                ),
            ],
        ),
        TransitionTrigger(
            TeamStateMachine.reapply,
            effects=[
                RelatedTransitionEffect(
                    "team_members",
                    TeamMemberStateMachine.reapply,
                ),
            ],
        ),
        TransitionTrigger(
            TeamStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    "team_members",
                    TeamMemberStateMachine.remove,
                ),
            ],
        ),
        TransitionTrigger(
            TeamStateMachine.readd,
            effects=[
                RelatedTransitionEffect(
                    "team_members",
                    TeamMemberStateMachine.readd,
                ),
            ],
        ),
        TransitionTrigger(
            TeamStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    "team_members",
                    TeamMemberStateMachine.remove,
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
        TransitionTrigger(
            TeamMemberStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    "participations",
                    TeamScheduleParticipantStateMachine.withdraw,
                ),
            ],
        ),
        TransitionTrigger(
            TeamMemberStateMachine.reapply,
            effects=[
                RelatedTransitionEffect(
                    "participations",
                    TeamScheduleParticipantStateMachine.reapply,
                ),
            ],
        ),
        TransitionTrigger(
            TeamMemberStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    "participations",
                    TeamScheduleParticipantStateMachine.remove,
                ),
            ],
        ),
        TransitionTrigger(
            TeamMemberStateMachine.readd,
            effects=[
                RelatedTransitionEffect(
                    "participations",
                    TeamScheduleParticipantStateMachine.readd,
                ),
            ],
        ),
    ]
