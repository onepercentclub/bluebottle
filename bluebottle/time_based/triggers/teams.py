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
from bluebottle.time_based.states.participants import ParticipantStateMachine
from bluebottle.time_based.states.participants import (
    TeamScheduleParticipantStateMachine,
)
from bluebottle.time_based.states.slots import TeamScheduleSlotStateMachine
from bluebottle.time_based.states.teams import (
    TeamStateMachine,
    TeamMemberStateMachine
)


@register(Team)
class TeamTriggers(TriggerManager):
    def should_auto_accept(effect):
        return not effect.instance.activity.review

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
            TeamStateMachine.rejoin,
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
                    "slots",
                    TeamScheduleSlotStateMachine.cancel,
                ),
                RelatedTransitionEffect(
                    "team_members",
                    TeamMemberStateMachine.cancel,
                ),
            ],
        ),
        TransitionTrigger(
            TeamStateMachine.restore,
            effects=[
                RelatedTransitionEffect(
                    "slots",
                    TeamScheduleSlotStateMachine.restore,
                ),
                RelatedTransitionEffect(
                    "team_members",
                    TeamMemberStateMachine.restore,
                ),
            ],
        ),
        TransitionTrigger(
            TeamStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    "slots",
                    TeamScheduleSlotStateMachine.cancel,
                ),
                RelatedTransitionEffect(
                    "team_members",
                    TeamMemberStateMachine.cancel,
                ),
            ],
        ),
        TransitionTrigger(
            TeamStateMachine.rejoin,
            effects=[
                RelatedTransitionEffect(
                    "slots",
                    TeamScheduleSlotStateMachine.restore,
                ),
                RelatedTransitionEffect(
                    "team_members",
                    TeamMemberStateMachine.restore,
                ),
            ],
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
                    ParticipantStateMachine.cancel,
                )
            ]
        ),
        TransitionTrigger(
            TeamMemberStateMachine.reapply,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    ParticipantStateMachine.restore,
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
        TransitionTrigger(
            TeamMemberStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    TeamScheduleParticipantStateMachine.withdraw,
                ),
            ],
        ),
        TransitionTrigger(
            TeamMemberStateMachine.reapply,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    TeamScheduleParticipantStateMachine.reapply,
                ),
            ],
        ),
        TransitionTrigger(
            TeamMemberStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    TeamScheduleParticipantStateMachine.remove,
                ),
            ],
        ),
        TransitionTrigger(
            TeamMemberStateMachine.readd,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    TeamScheduleParticipantStateMachine.readd,
                ),
            ],
        ),
    ]
