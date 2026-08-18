from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import (
    register,
    TransitionTrigger,
    TriggerManager,
    ModelDeletedTrigger
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.activity_pub.effects import (
    SendTeamJoinEffect,
    SendAddToTeamEffect,
    SendTeamLeaveEffect,
    SendTeamMemberLeaveEffect,
    SyncRelatedEvent,
)
from bluebottle.time_based.effects.teams import (
    CreateTeamRegistrationEffect,
    CreateCaptainTeamMemberEffect,
    CreateTeamSlotEffect,
    CreateTeamMemberSlotParticipantsEffect,
    DeleteTeamMemberSlotParticipantsEffect,
)
from bluebottle.time_based.messages.teams import (
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
from bluebottle.time_based.models import Team, TeamMember
from bluebottle.time_based.states.participants import (
    TeamScheduleParticipantStateMachine,
)
from bluebottle.time_based.states.registrations import RegistrationStateMachine
from bluebottle.time_based.states.slots import TeamScheduleSlotStateMachine
from bluebottle.time_based.states.teams import TeamStateMachine, TeamMemberStateMachine


@register(Team)
class TeamTriggers(TriggerManager):
    def should_auto_accept(effect):
        """ Check if the team should be auto accepted """
        user = effect.options.get('user')
        is_admin = (
            user and
            (not hasattr(effect.instance, 'user') or effect.instance.user != user) and
            (user.is_staff or user.is_superuser)
        )
        registration = getattr(effect.instance, 'registration', None)
        registration_accepted = registration and registration.status == 'accepted'

        # Adopted activities wait for supplier Accept of the registration Join.
        if getattr(effect.instance.activity, 'is_adopted', False):
            return registration_accepted or is_admin

        return (
            not effect.instance.activity.review or
            registration_accepted or
            is_admin
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
                SendTeamJoinEffect,
                SyncRelatedEvent,
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
                RelatedTransitionEffect(
                    "registration",
                    RegistrationStateMachine.withdraw,
                ),
                NotificationEffect(UserTeamWithdrewNotification),
                NotificationEffect(ManagerTeamWithdrewNotification),
                SendTeamLeaveEffect,
                SyncRelatedEvent,
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
                RelatedTransitionEffect(
                    "registration",
                    RegistrationStateMachine.restore,
                ),
                SendTeamJoinEffect,
                SyncRelatedEvent,
            ]
        ),
    ]


@register(TeamMember)
class TeamMemberTriggers(TriggerManager):
    def is_not_captain(effect):
        return not effect.instance.is_captain

    triggers = [
        TransitionTrigger(
            TeamMemberStateMachine.initiate,
            effects=[
                CreateTeamMemberSlotParticipantsEffect,
                NotificationEffect(
                    UserTeamMemberJoinedNotification,
                    conditions=[is_not_captain],
                ),
                NotificationEffect(
                    CaptainTeamMemberJoinedNotification,
                    conditions=[is_not_captain],
                ),
                SendAddToTeamEffect,
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
                SendTeamMemberLeaveEffect,
            ],
        ),
        TransitionTrigger(
            TeamMemberStateMachine.reapply,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    TeamScheduleParticipantStateMachine.reapply,
                ),
                SendAddToTeamEffect,
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
                SendAddToTeamEffect,
            ],
        ),
        TransitionTrigger(
            TeamMemberStateMachine.reject,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    TeamScheduleParticipantStateMachine.reject,
                ),
            ],
        ),
        TransitionTrigger(
            TeamMemberStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    TeamScheduleParticipantStateMachine.accept,
                ),
                SendAddToTeamEffect,
            ],
        ),
        TransitionTrigger(
            TeamMemberStateMachine.resume,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    TeamScheduleParticipantStateMachine.reapply,
                ),
                RelatedTransitionEffect(
                    'participants',
                    TeamScheduleParticipantStateMachine.readd,
                ),
                RelatedTransitionEffect(
                    'participants',
                    TeamScheduleParticipantStateMachine.accept,
                ),
                SendAddToTeamEffect,
            ],
        ),
    ]
