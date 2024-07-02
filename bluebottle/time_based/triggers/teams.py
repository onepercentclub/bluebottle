from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import (
    register,
    TransitionTrigger,
    TriggerManager,
    ModelDeletedTrigger
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects.teams import (
    CreateTeamRegistrationEffect,
    CreateCaptainTeamMemberEffect,
    CreateTeamSlotEffect,
    CreateTeamMemberSlotParticipantsEffect,
    DeleteTeamMemberSlotParticipantsEffect,
)
from bluebottle.time_based.models import Team, TeamMember
from bluebottle.time_based.notifications.teams import (
    CaptainTeamMemberJoinedNotification,
    ManagerTeamRemovedNotification,
    UserTeamMemberJoinedNotification,
    UserTeamRemovedNotification,
    UserTeamWithdrewNotification,
    ManagerTeamWithdrewNotification,
    UserTeamScheduledNotification,
    CaptainTeamMemberWithdrewNotification,
    UserTeamMemberWithdrewNotification,
    CaptainTeamMemberRemovedNotification,
    UserTeamMemberRemovedNotification,
)
from bluebottle.time_based.states.participants import (
    TeamScheduleParticipantStateMachine,
)
from bluebottle.time_based.states.slots import TeamScheduleSlotStateMachine
from bluebottle.time_based.states.teams import TeamStateMachine, TeamMemberStateMachine


@register(Team)
class TeamTriggers(TriggerManager):
    def should_auto_accept(effect):
        """ Check if the team should be auto accepted """
        user = effect.options.get('user')
        is_admin = user and effect.instance.user != user and (user.is_staff or user.is_superuser)
        return (
            not effect.instance.activity.review or is_admin
        )

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
            TeamStateMachine.schedule,
            effects=[
                NotificationEffect(UserTeamScheduledNotification),
            ],
        ),
        TransitionTrigger(
            TeamStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    "slots",
                    TeamScheduleSlotStateMachine.auto_cancel,
                ),
                RelatedTransitionEffect(
                    "team_members",
                    TeamMemberStateMachine.auto_remove,
                ),
                NotificationEffect(UserTeamRemovedNotification),
                NotificationEffect(ManagerTeamRemovedNotification),
            ],
        ),
        TransitionTrigger(
            TeamStateMachine.readd,
            effects=[
                RelatedTransitionEffect(
                    "team_members",
                    TeamMemberStateMachine.readd,
                ),
                RelatedTransitionEffect(
                    "slots",
                    TeamScheduleSlotStateMachine.restore,
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
                    "team_members",
                    TeamMemberStateMachine.withdraw,
                ),
                NotificationEffect(UserTeamWithdrewNotification),
                NotificationEffect(ManagerTeamWithdrewNotification),
            ],
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
                    TeamMemberStateMachine.reapply,
                ),
            ]
        ),
    ]


@register(TeamMember)
class TeamMemberTriggers(TriggerManager):
    def is_not_self(self):
        user = self.options.get('user')
        return self.instance.user != user and self.instance.activity.owner != user

    triggers = [
        TransitionTrigger(
            TeamMemberStateMachine.initiate,
            effects=[
                CreateTeamMemberSlotParticipantsEffect,
                NotificationEffect(
                    UserTeamMemberJoinedNotification,
                    conditions=[is_not_self],
                ),
                NotificationEffect(
                    CaptainTeamMemberJoinedNotification,
                    conditions=[is_not_self],
                ),
            ]
        ),
        TransitionTrigger(
            TeamMemberStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    TeamScheduleParticipantStateMachine.withdraw,
                ),
                NotificationEffect(
                    CaptainTeamMemberWithdrewNotification
                ),
                NotificationEffect(
                    UserTeamMemberWithdrewNotification
                ),
            ],
        ),
        TransitionTrigger(
            TeamMemberStateMachine.reapply,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    TeamScheduleParticipantStateMachine.restore,
                )
            ]
        ),
        TransitionTrigger(
            TeamMemberStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    TeamScheduleParticipantStateMachine.cancel,
                )
            ]
        ),
        TransitionTrigger(
            TeamMemberStateMachine.restore,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    TeamScheduleParticipantStateMachine.restore,
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
            TeamMemberStateMachine.auto_remove,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    TeamScheduleParticipantStateMachine.auto_remove,
                ),
            ],
        ),
        TransitionTrigger(
            TeamMemberStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    TeamScheduleParticipantStateMachine.auto_remove,
                ),
                NotificationEffect(
                    CaptainTeamMemberRemovedNotification
                ),
                NotificationEffect(
                    UserTeamMemberRemovedNotification
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
