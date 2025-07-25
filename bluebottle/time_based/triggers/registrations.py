from bluebottle.activities.messages.participant import InactiveParticipantAddedNotification
from bluebottle.follow.effects import FollowActivityEffect, UnFollowActivityEffect
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import TransitionTrigger, TriggerManager, register
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects import LockFilledSlotsEffect
from bluebottle.time_based.effects.registrations import (
    CreateInitialPeriodicParticipantEffect,
    CreateParticipantEffect,
    CreateTeamEffect, AdjustInitialPeriodicParticipantEffect, CreateSlotParticipantEffect
)
from bluebottle.time_based.messages import (
    ParticipantAddedNotification,
    ManagerParticipantAddedOwnerNotification,
    TeamAddedNotification,
    ManagerTeamAddedOwnerNotification,
)
from bluebottle.time_based.messages.registrations import (
    ManagerRegistrationCreatedNotification,
    ManagerRegistrationCreatedReviewNotification,
    ManagerTeamRegistrationCreatedNotification,
    ManagerTeamRegistrationCreatedReviewNotification,
    TeamAppliedNotification,
    TeamJoinedNotification,
    UserRegistrationAcceptedNotification,
    UserTeamRegistrationAcceptedNotification,
    UserRegistrationRejectedNotification,
    UserRegistrationRemovedNotification,
    UserTeamRegistrationRejectedNotification,
    UserRegistrationRestartedNotification,
    UserRegistrationStoppedNotification,
    ManagerRegistrationStoppedNotification,
    ManagerRegistrationRestartedNotification, DeadlineUserAppliedNotification, DeadlineUserJoinedNotification,
    PeriodicUserAppliedNotification, PeriodicUserJoinedNotification, ScheduleUserAppliedNotification,
    ScheduleUserJoinedNotification, DateUserAppliedNotification, )
from bluebottle.time_based.models import (
    DeadlineRegistration,
    PeriodicRegistration,
    ScheduleRegistration,
    TeamScheduleRegistration,
    DateRegistration,
)
from bluebottle.time_based.states import (
    DeadlineParticipantStateMachine,
    RegistrationStateMachine,
    TeamStateMachine,
    ScheduleActivityStateMachine, )
from bluebottle.time_based.states.participants import (
    PeriodicParticipantStateMachine,
    RegistrationParticipantStateMachine,
    ScheduleParticipantStateMachine,
    TeamScheduleParticipantStateMachine,
)
from bluebottle.time_based.states.registrations import (
    PeriodicRegistrationStateMachine,
    ScheduleRegistrationStateMachine,
)
from bluebottle.time_based.states.states import PeriodicActivityStateMachine


def review_needed(effect):
    """Review needed"""
    return effect.instance.activity.review


def no_review_needed(effect):
    """No review needed"""
    return not effect.instance.activity.review


def is_user(effect):
    """Is user"""
    user = effect.options.get("user")
    return effect.instance.user == user


def is_admin(effect):
    """Is not user"""
    user = effect.options.get("user")
    return (
        user and effect.instance.user != user and (user.is_staff or user.is_superuser)
    )


def participant_is_active(effect):
    from bluebottle.members.models import MemberPlatformSettings
    settings = MemberPlatformSettings.load()
    return settings.closed or effect.instance.user.is_active


def participant_is_inactive(effect):
    return not participant_is_active(effect)


class RegistrationTriggers(TriggerManager):

    triggers = [
        TransitionTrigger(
            RegistrationStateMachine.initiate,
            effects=[
                TransitionEffect(
                    RegistrationStateMachine.auto_accept,
                    conditions=[
                        no_review_needed,
                        is_user
                    ]
                ),
                TransitionEffect(
                    RegistrationStateMachine.add,
                    conditions=[
                        is_admin
                    ]
                ),
            ]
        ),
        TransitionTrigger(
            RegistrationStateMachine.auto_accept,
            effects=[
                FollowActivityEffect,
            ]
        ),
        TransitionTrigger(
            RegistrationStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    RegistrationParticipantStateMachine.accept,
                ),
                FollowActivityEffect,
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.auto_accept,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    RegistrationParticipantStateMachine.accept,
                ),
            ]
        ),
        TransitionTrigger(
            RegistrationStateMachine.auto_accept,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    RegistrationParticipantStateMachine.accept,
                ),
            ]
        ),
        TransitionTrigger(
            RegistrationStateMachine.reject,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    RegistrationParticipantStateMachine.reject,
                ),
                UnFollowActivityEffect,
            ]
        )

    ]


@register(DeadlineRegistration)
class DeadlineRegistrationTriggers(RegistrationTriggers):
    triggers = RegistrationTriggers.triggers + [
        TransitionTrigger(
            RegistrationStateMachine.initiate,
            effects=[
                CreateParticipantEffect,
                NotificationEffect(
                    ManagerRegistrationCreatedReviewNotification,
                    conditions=[review_needed, is_user],
                ),
                NotificationEffect(
                    DeadlineUserAppliedNotification, conditions=[review_needed, is_user]
                ),
                NotificationEffect(
                    ManagerRegistrationCreatedNotification,
                    conditions=[no_review_needed, is_user],
                ),
                NotificationEffect(
                    DeadlineUserJoinedNotification, conditions=[no_review_needed, is_user]
                ),
            ]
        ),
        TransitionTrigger(
            RegistrationStateMachine.add,
            effects=[
                NotificationEffect(
                    ParticipantAddedNotification,
                    conditions=[participant_is_active]
                ),
                NotificationEffect(
                    InactiveParticipantAddedNotification,
                    conditions=[participant_is_inactive]
                ),
                NotificationEffect(
                    ManagerParticipantAddedOwnerNotification,
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    DeadlineParticipantStateMachine.accept,
                ),
                NotificationEffect(
                    UserRegistrationAcceptedNotification,
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.auto_accept,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    DeadlineParticipantStateMachine.accept,
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.reject,
            effects=[
                NotificationEffect(
                    UserRegistrationRejectedNotification,
                ),
            ],
        ),
    ]


@register(PeriodicRegistration)
class PeriodicRegistrationTriggers(RegistrationTriggers):
    def activity_no_spots_left(effect):
        """Activity has spots available after this effect"""
        if not effect.instance.activity.capacity:
            return False
        accepted = effect.instance.activity.registrations.filter(
            status="accepted"
        ).count()
        return effect.instance.activity.capacity <= accepted + 1

    def activity_spots_left(effect):
        """Activity has spots available after this effect"""
        if not effect.instance.activity.capacity:
            return True
        accepted = effect.instance.activity.registrations.filter(
            status="accepted"
        ).count()
        return effect.instance.activity.capacity > accepted - 1

    triggers = RegistrationTriggers.triggers + [
        TransitionTrigger(
            RegistrationStateMachine.initiate,
            effects=[
                CreateInitialPeriodicParticipantEffect,
                NotificationEffect(
                    ManagerRegistrationCreatedReviewNotification,
                    conditions=[review_needed, is_user],
                ),
                NotificationEffect(
                    PeriodicUserAppliedNotification, conditions=[review_needed, is_user]
                ),
                NotificationEffect(
                    ManagerRegistrationCreatedNotification,
                    conditions=[no_review_needed, is_user],
                ),
                NotificationEffect(
                    PeriodicUserJoinedNotification, conditions=[no_review_needed, is_user]
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.add,
            effects=[
                NotificationEffect(
                    ParticipantAddedNotification,
                    conditions=[participant_is_active]
                ),
                NotificationEffect(
                    InactiveParticipantAddedNotification,
                    conditions=[participant_is_inactive]
                ),
                NotificationEffect(
                    ManagerParticipantAddedOwnerNotification,
                ),
            ],
        ),
        TransitionTrigger(
            PeriodicRegistrationStateMachine.auto_accept,
            effects=[
                RelatedTransitionEffect(
                    "activity",
                    PeriodicActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
                AdjustInitialPeriodicParticipantEffect,
            ],
        ),
        TransitionTrigger(
            PeriodicRegistrationStateMachine.add,
            effects=[
                RelatedTransitionEffect(
                    "activity",
                    PeriodicActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
                AdjustInitialPeriodicParticipantEffect,
            ],
        ),
        TransitionTrigger(
            PeriodicRegistrationStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    "activity",
                    PeriodicActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
                AdjustInitialPeriodicParticipantEffect,
                NotificationEffect(
                    UserRegistrationAcceptedNotification,
                ),
            ],
        ),
        TransitionTrigger(
            PeriodicRegistrationStateMachine.reject,
            effects=[
                RelatedTransitionEffect(
                    "activity",
                    PeriodicActivityStateMachine.unlock,
                    conditions=[activity_spots_left],
                ),
                NotificationEffect(
                    UserRegistrationRejectedNotification,
                ),
            ],
        ),
        TransitionTrigger(
            PeriodicRegistrationStateMachine.start,
            effects=[
                NotificationEffect(UserRegistrationRestartedNotification),
                NotificationEffect(ManagerRegistrationRestartedNotification),
                RelatedTransitionEffect(
                    "activity",
                    PeriodicActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
            ],
        ),
        TransitionTrigger(
            PeriodicRegistrationStateMachine.stop,
            effects=[
                NotificationEffect(UserRegistrationStoppedNotification),
                NotificationEffect(ManagerRegistrationStoppedNotification),
                RelatedTransitionEffect(
                    "activity",
                    PeriodicActivityStateMachine.unlock,
                    conditions=[activity_spots_left],
                ),
            ],
        ),

        TransitionTrigger(
            PeriodicRegistrationStateMachine.remove,
            effects=[
                UnFollowActivityEffect,
                NotificationEffect(UserRegistrationRemovedNotification),
                RelatedTransitionEffect(
                    "activity",
                    PeriodicActivityStateMachine.unlock,
                    conditions=[activity_spots_left],
                ),
                RelatedTransitionEffect(
                    "participants",
                    PeriodicParticipantStateMachine.auto_remove,
                ),
            ],
        ),
    ]


@register(ScheduleRegistration)
class ScheduleRegistrationTriggers(RegistrationTriggers):
    triggers = RegistrationTriggers.triggers + [
        TransitionTrigger(
            RegistrationStateMachine.initiate,
            effects=[
                CreateParticipantEffect,
                NotificationEffect(
                    ManagerRegistrationCreatedReviewNotification,
                    conditions=[review_needed, is_user],
                ),
                NotificationEffect(
                    ScheduleUserAppliedNotification, conditions=[review_needed, is_user]
                ),
                NotificationEffect(
                    ManagerRegistrationCreatedNotification,
                    conditions=[no_review_needed, is_user],
                ),
                NotificationEffect(
                    ScheduleUserJoinedNotification, conditions=[no_review_needed, is_user]
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.add,
            effects=[
                NotificationEffect(
                    ParticipantAddedNotification,
                    conditions=[participant_is_active]
                ),
                NotificationEffect(
                    InactiveParticipantAddedNotification,
                    conditions=[participant_is_inactive]
                ),
                NotificationEffect(
                    ManagerParticipantAddedOwnerNotification,
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    ScheduleParticipantStateMachine.accept,
                ),
                NotificationEffect(
                    UserRegistrationAcceptedNotification,
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleRegistrationStateMachine.auto_accept,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    ScheduleParticipantStateMachine.accept,
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.reject,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    ScheduleParticipantStateMachine.reject,
                ),
                NotificationEffect(
                    UserRegistrationRejectedNotification,
                ),
            ],
        ),
    ]


@register(TeamScheduleRegistration)
class TeamScheduleRegistrationTriggers(RegistrationTriggers):
    def activity_no_spots_left(effect):
        """Activity has spots available after this effect"""
        if not effect.instance.activity.capacity:
            return False

        accepted = effect.instance.activity.registrations.filter(
            status="accepted"
        ).count()

        return effect.instance.activity.capacity <= accepted + 1

    def activity_spots_left(effect):
        """Activity has spots available after this effect"""
        if not effect.instance.activity.capacity:
            return True

        accepted = effect.instance.activity.registrations.filter(
            status="accepted"
        ).count()
        return effect.instance.activity.capacity > accepted - 1

    triggers = RegistrationTriggers.triggers + [
        TransitionTrigger(
            RegistrationStateMachine.initiate,
            effects=[
                CreateTeamEffect,
                NotificationEffect(
                    ManagerTeamRegistrationCreatedReviewNotification,
                    conditions=[review_needed, is_user],
                ),
                NotificationEffect(
                    ManagerTeamRegistrationCreatedNotification,
                    conditions=[no_review_needed, is_user],
                ),
                NotificationEffect(
                    TeamAppliedNotification, conditions=[review_needed, is_user]
                ),
                NotificationEffect(
                    TeamJoinedNotification, conditions=[no_review_needed, is_user]
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.add,
            effects=[
                NotificationEffect(
                    TeamAddedNotification,
                ),
                NotificationEffect(
                    ManagerTeamAddedOwnerNotification,
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    "team",
                    TeamStateMachine.accept,
                ),
                RelatedTransitionEffect(
                    "participants",
                    TeamScheduleParticipantStateMachine.accept,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
                NotificationEffect(
                    UserTeamRegistrationAcceptedNotification,
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleRegistrationStateMachine.auto_accept,
            effects=[
                RelatedTransitionEffect(
                    "team",
                    TeamStateMachine.accept,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleRegistrationStateMachine.add,
            effects=[
                RelatedTransitionEffect(
                    "team",
                    TeamStateMachine.accept,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.reject,
            effects=[
                RelatedTransitionEffect(
                    "team",
                    TeamStateMachine.reject,
                ),
                RelatedTransitionEffect(
                    "participants",
                    TeamScheduleParticipantStateMachine.reject,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.unlock,
                    conditions=[activity_spots_left],
                ),
                NotificationEffect(
                    UserTeamRegistrationRejectedNotification,
                ),
            ],
        ),
    ]


@register(DateRegistration)
class DateRegistrationTriggers(RegistrationTriggers):
    triggers = RegistrationTriggers.triggers + [
        TransitionTrigger(
            RegistrationStateMachine.initiate,
            effects=[
                NotificationEffect(
                    ManagerRegistrationCreatedReviewNotification,
                    conditions=[review_needed, is_user],
                ),
                NotificationEffect(
                    DateUserAppliedNotification,
                    conditions=[
                        review_needed,
                        is_user
                    ]
                ),
            ]
        ),
        TransitionTrigger(
            RegistrationStateMachine.add,
            effects=[
                CreateSlotParticipantEffect,
                NotificationEffect(
                    ParticipantAddedNotification,
                ),
                NotificationEffect(
                    ManagerParticipantAddedOwnerNotification,
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.accept,
            effects=[
                NotificationEffect(
                    UserRegistrationAcceptedNotification,
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.auto_accept,
            effects=[
                LockFilledSlotsEffect,
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.reject,
            effects=[
                NotificationEffect(
                    UserRegistrationRejectedNotification,
                ),
            ],
        ),
    ]
