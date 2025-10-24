from django.utils.timezone import now

from bluebottle.activities.messages.participant import InactiveParticipantAddedNotification
from bluebottle.activities.states import ContributionStateMachine
from bluebottle.activities.triggers import (
    ContributorTriggers
)
from bluebottle.follow.effects import FollowActivityEffect, UnFollowActivityEffect
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    TransitionTrigger,
    register,
    ModelChangedTrigger, ModelDeletedTrigger,
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects import CreatePreparationTimeContributionEffect, CreateSlotTimeContributionEffect, \
    CheckPreparationTimeContributionEffect, SlotParticipantUnFollowActivityEffect
from bluebottle.time_based.effects.effects import (
    CreateSchedulePreparationTimeContributionEffect,
)
from bluebottle.time_based.effects.participants import (
    CreateScheduleContributionEffect,
    CreateTimeContributionEffect,
    CreateRegistrationEffect,
    CreatePeriodicPreparationTimeContributionEffect, CreateScheduleSlotEffect, CreateDateRegistrationEffect,
    CreateRegisteredTimeContributionEffect,
)
from bluebottle.time_based.effects.registrations import DeleteRegistrationEffect
from bluebottle.time_based.messages import (
    ParticipantAddedNotification, ManagerSlotParticipantRegisteredNotification,
    ParticipantSlotParticipantRegisteredNotification, ParticipantChangedNotification,
    ManagerSlotParticipantWithdrewNotification,
)
from bluebottle.time_based.models import (
    DeadlineParticipant,
    PeriodicParticipant, ScheduleParticipant, TeamScheduleParticipant, DateParticipant, RegisteredDateParticipant,
)
from bluebottle.time_based.messages.participants import (
    ManagerParticipantRemovedNotification,
    UserParticipantRemovedNotification,
    UserParticipantWithdrewNotification,
    ManagerParticipantWithdrewNotification, UserScheduledNotification, RegisteredActivityParticipantAddedNotification,
    UserDateParticipantWithdrewNotification,
)
from bluebottle.time_based.states import (
    ParticipantStateMachine,
    DeadlineParticipantStateMachine,
    DeadlineActivityStateMachine,
    RegistrationActivityStateMachine,
    PeriodicParticipantStateMachine,
    ScheduleParticipantStateMachine,
    ScheduleActivityStateMachine,
    TeamScheduleParticipantStateMachine, TeamMemberStateMachine, RegistrationParticipantStateMachine,
    DateParticipantStateMachine, TimeContributionStateMachine, DateActivitySlotStateMachine,
    RegisteredDateParticipantStateMachine, RegisteredDateActivityStateMachine, DateStateMachine,
    RegistrationStateMachine
)


def activity_is_expired(effect):
    """Activity is expired"""
    return effect.instance.activity.status == "expired"


def activity_will_be_expired(effect):
    """Activity is expired"""

    return (
        effect.instance.activity.status == "succeeded"
        and effect.instance.activity.active_participants.count() == 1
    )


def participant_is_active(effect):
    from bluebottle.members.models import MemberPlatformSettings

    settings = MemberPlatformSettings.load()
    return (not settings.closed) and effect.instance.user.is_active


def participant_is_inactive(effect):
    return not participant_is_active(effect)


class RegistrationParticipantTriggers(ContributorTriggers):

    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            RegistrationParticipantStateMachine.succeed,
            effects=[
                FollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.succeed,
                ),
                RelatedTransitionEffect(
                    "activity",
                    RegistrationActivityStateMachine.succeed,
                    conditions=[activity_is_expired],
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationParticipantStateMachine.accept,
            effects=[
                FollowActivityEffect,
                RelatedTransitionEffect(
                    "activity",
                    RegistrationActivityStateMachine.succeed,
                    conditions=[activity_is_expired],
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationParticipantStateMachine.reject,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    "activity",
                    RegistrationActivityStateMachine.expire,
                    conditions=[activity_will_be_expired],
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationParticipantStateMachine.cancel,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationParticipantStateMachine.withdraw,
            effects=[
                NotificationEffect(UserParticipantWithdrewNotification),
                NotificationEffect(ManagerParticipantWithdrewNotification),
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    "activity",
                    DeadlineActivityStateMachine.expire,
                    conditions=[activity_will_be_expired],
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationParticipantStateMachine.reapply,
            effects=[
                FollowActivityEffect,
                RelatedTransitionEffect(
                    "activity",
                    DeadlineActivityStateMachine.succeed,
                    conditions=[activity_is_expired],
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationParticipantStateMachine.remove,
            effects=[
                NotificationEffect(UserParticipantRemovedNotification),
                NotificationEffect(ManagerParticipantRemovedNotification),
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    "activity",
                    DeadlineActivityStateMachine.expire,
                    conditions=[activity_will_be_expired],
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationParticipantStateMachine.auto_remove,
            effects=[
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
            ],
        ),
        TransitionTrigger(
            RegistrationParticipantStateMachine.restore,
            effects=[
                FollowActivityEffect,
                RelatedTransitionEffect(
                    'contributions',
                    ContributionStateMachine.reset,
                ),
                RelatedTransitionEffect(
                    "activity",
                    DeadlineActivityStateMachine.succeed,
                    conditions=[activity_is_expired],
                ),
            ],
        ),
    ]


@register(DeadlineParticipant)
class DeadlineParticipantTriggers(RegistrationParticipantTriggers):
    def registration_is_accepted(effect):
        """Review needed"""
        return (
            effect.instance.registration and
            effect.instance.registration.status == "accepted"
        )

    def is_admin(effect):
        """ Is admin """
        user = effect.options.get('user', None)
        return user and (user.is_staff or user.is_superuser) and effect.instance.user != user

    def is_user(effect):
        """ Is user """
        user = effect.options.get('user', None)
        return user == effect.instance.user

    def activity_no_spots_left(effect):
        """ Activity has spots available after this effect """
        if not effect.instance.activity.capacity:
            return False
        return effect.instance.activity.capacity <= effect.instance.activity.accepted_participants.count() + 1

    def activity_spots_left(effect):
        """ Activity has spots available after this effect """
        if not effect.instance.activity.capacity:
            return True
        return effect.instance.activity.capacity > effect.instance.activity.accepted_participants.count() - 1

    def activity_has_started(effect):
        """ Activity has started """
        if effect.instance.activity.start:
            return effect.instance.activity.start < now().date()
        return True

    def is_not_self(self):
        "Participant is created by other user"
        user = self.options.get('user')

        return user and self.instance.user != user

    triggers = RegistrationParticipantTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                FollowActivityEffect,
                CreateRegistrationEffect,
                CreateTimeContributionEffect,
                CreatePreparationTimeContributionEffect,
                TransitionEffect(
                    DeadlineParticipantStateMachine.add,
                    conditions=[is_not_self],
                ),
                TransitionEffect(
                    DeadlineParticipantStateMachine.accept,
                    conditions=[registration_is_accepted],
                ),
            ],
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.accept,
            effects=[
                FollowActivityEffect,
                TransitionEffect(DeadlineParticipantStateMachine.succeed),
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.succeed,
                ),
                RelatedTransitionEffect(
                    'activity',
                    DeadlineActivityStateMachine.lock,
                    conditions=[
                        activity_no_spots_left
                    ]
                )
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.add,
            effects=[
                CreateRegistrationEffect,
                NotificationEffect(
                    ParticipantAddedNotification,
                    conditions=[participant_is_active]
                ),
                NotificationEffect(
                    InactiveParticipantAddedNotification,
                    conditions=[participant_is_inactive]
                ),
                TransitionEffect(
                    DeadlineParticipantStateMachine.succeed,
                    conditions=[
                        activity_has_started
                    ]
                ),
                RelatedTransitionEffect(
                    'activity',
                    DeadlineActivityStateMachine.lock,
                    conditions=[
                        activity_no_spots_left
                    ]
                ),
                RelatedTransitionEffect(
                    "activity",
                    RegistrationActivityStateMachine.succeed,
                    conditions=[activity_is_expired],
                ),
            ]
        ),
        TransitionTrigger(
            RegistrationParticipantStateMachine.readd,
            effects=[
                TransitionEffect(
                    DeadlineParticipantStateMachine.succeed,
                    conditions=[
                        registration_is_accepted,
                    ],
                ),
                RelatedTransitionEffect(
                    'activity',
                    DeadlineActivityStateMachine.lock,
                    conditions=[
                        activity_no_spots_left
                    ]
                ),
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    DeadlineActivityStateMachine.lock,
                    conditions=[
                        activity_no_spots_left
                    ]
                )
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    DeadlineActivityStateMachine.unlock,
                    conditions=[
                        activity_spots_left
                    ]
                )
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.restore,
            effects=[
                TransitionEffect(
                    DeadlineParticipantStateMachine.succeed,
                    conditions=[
                        registration_is_accepted,
                    ],
                ),
                RelatedTransitionEffect(
                    "activity",
                    DeadlineActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
            ],
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.reapply,
            effects=[
                TransitionEffect(
                    DeadlineParticipantStateMachine.succeed,
                    conditions=[
                        registration_is_accepted,
                    ]
                ),
                RelatedTransitionEffect(
                    'activity',
                    DeadlineActivityStateMachine.lock,
                    conditions=[
                        activity_no_spots_left
                    ]
                )
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.restore,
            effects=[
                FollowActivityEffect,
                TransitionEffect(
                    DeadlineParticipantStateMachine.succeed,
                    conditions=[
                        registration_is_accepted,
                    ],
                ),
                RelatedTransitionEffect(
                    "activity",
                    DeadlineActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
            ],
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    DeadlineActivityStateMachine.unlock,
                    conditions=[
                        activity_spots_left
                    ]
                )
            ],
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.fail,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    'contributions',
                    ContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    'activity',
                    DeadlineActivityStateMachine.unlock,
                    conditions=[
                        activity_spots_left
                    ]
                )
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.reject,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    'contributions',
                    ContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    'activity',
                    DeadlineActivityStateMachine.unlock,
                    conditions=[
                        activity_spots_left
                    ]
                )
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.cancelled,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    DeadlineActivityStateMachine.unlock,
                    conditions=[
                        activity_spots_left
                    ]
                )
            ]
        ),
    ]


@register(PeriodicParticipant)
class PeriodicParticipantTriggers(RegistrationParticipantTriggers):
    def slot_is_finished(effect):
        """Slot has status finished"""
        return effect.instance.slot and effect.instance.slot.status == "finished"

    def registration_is_accepted(effect):
        """Review needed"""
        return (
            effect.instance.registration
            and effect.instance.registration.status == "accepted"
        )

    triggers = RegistrationParticipantTriggers.triggers + [
        TransitionTrigger(
            PeriodicParticipantStateMachine.initiate,
            effects=[
                CreateTimeContributionEffect,
                CreatePeriodicPreparationTimeContributionEffect,
                TransitionEffect(
                    PeriodicParticipantStateMachine.succeed,
                    conditions=[slot_is_finished],
                ),
            ],
        ),
        TransitionTrigger(
            PeriodicParticipantStateMachine.accept,
            effects=[
                FollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.reset,
                ),
                TransitionEffect(
                    PeriodicParticipantStateMachine.succeed,
                    conditions=[slot_is_finished],
                ),
            ],
        ),
        TransitionTrigger(
            PeriodicParticipantStateMachine.reject,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
            ],
        ),
        TransitionTrigger(
            PeriodicParticipantStateMachine.restore,
            effects=[
                TransitionEffect(
                    PeriodicParticipantStateMachine.succeed,
                    conditions=[slot_is_finished],
                )
            ],
        ),
        TransitionTrigger(
            PeriodicParticipantStateMachine.readd,
            effects=[
                FollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.reset,
                ),
                TransitionEffect(
                    PeriodicParticipantStateMachine.succeed,
                    conditions=[slot_is_finished],
                )
            ],
        ),
        TransitionTrigger(
            PeriodicParticipantStateMachine.reapply,
            effects=[
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.reset,
                ),
                TransitionEffect(
                    PeriodicParticipantStateMachine.succeed,
                    conditions=[slot_is_finished],
                )
            ],
        ),
    ]


@register(ScheduleParticipant)
class ScheduleParticipantTriggers(RegistrationParticipantTriggers):

    def is_accepted(effect):
        """Review needed"""
        return (
            effect.instance.registration
            and effect.instance.registration.status == "accepted"
        ) or (
            effect.instance.team
            and effect.instance.team.status == "accepted"
        )

    def is_admin(effect):
        """Is admin"""
        user = effect.options.get("user", None)
        return (
            user
            and (user.is_staff or user.is_superuser)
            and effect.instance.user != user
        )

    def is_user(effect):
        """Is user"""
        user = effect.options.get("user", None)
        return user == effect.instance.user

    def activity_no_spots_left(effect):
        """Activity has spots available after this effect"""
        if not effect.instance.activity.capacity:
            return False
        return (
            effect.instance.activity.capacity
            <= effect.instance.activity.accepted_participants.count() + 1
        )

    def activity_spots_left(effect):
        """Activity has spots available after this effect"""
        if not effect.instance.activity.capacity:
            return True
        return (
            effect.instance.activity.capacity
            > effect.instance.activity.accepted_participants.count() - 1
        )

    def has_scheduled_slot(effect):
        """Has assigned slot"""
        return effect.instance.slot and effect.instance.slot.end

    def slot_is_finished(effect):
        """Has assigned slot"""
        return effect.instance.slot and effect.instance.slot.end and effect.instance.slot.end < now()

    def has_no_slot(effect):
        """Has no assigned slot"""
        return not effect.instance.slot or not effect.instance.slot.end

    def is_not_self(self):
        "Participant is created by other user"
        user = self.options.get('user')
        return user and self.instance.user != user

    triggers = RegistrationParticipantTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                CreateSchedulePreparationTimeContributionEffect,
                CreateScheduleContributionEffect,
                CreateRegistrationEffect,
                CreateScheduleSlotEffect,
                TransitionEffect(
                    ScheduleParticipantStateMachine.add,
                    conditions=[is_not_self],
                ),
                TransitionEffect(
                    ScheduleParticipantStateMachine.accept,
                    conditions=[is_accepted],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.accept,
            effects=[
                FollowActivityEffect,
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.reset,
                ),
                TransitionEffect(
                    ScheduleParticipantStateMachine.schedule,
                    conditions=[has_scheduled_slot]
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.add,
            effects=[
                CreateRegistrationEffect,
                NotificationEffect(
                    ParticipantAddedNotification,
                    conditions=[is_not_self, participant_is_active]
                ),
                NotificationEffect(
                    InactiveParticipantAddedNotification,
                    conditions=[is_not_self, participant_is_inactive]
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.readd,
            effects=[
                FollowActivityEffect,
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.succeed,
                ),
                RelatedTransitionEffect(
                    "activity",
                    RegistrationActivityStateMachine.succeed,
                    conditions=[activity_is_expired],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.reset,
            effects=[
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.reset,
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.withdraw,
            effects=[
                NotificationEffect(UserParticipantWithdrewNotification),
                NotificationEffect(ManagerParticipantWithdrewNotification),
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.unlock,
                    conditions=[activity_spots_left],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.restore,
            effects=[
                TransitionEffect(
                    ScheduleParticipantStateMachine.accept,
                    conditions=[
                        is_accepted,
                    ],
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.reapply,
            effects=[
                FollowActivityEffect,
                TransitionEffect(
                    ScheduleParticipantStateMachine.accept,
                    conditions=[
                        is_accepted,
                    ],
                ),
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.reset,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.readd,
            effects=[
                TransitionEffect(
                    ScheduleParticipantStateMachine.accept,
                    conditions=[
                        is_accepted,
                    ],
                ),
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.reset,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.remove,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
                NotificationEffect(UserParticipantRemovedNotification),
                NotificationEffect(ManagerParticipantRemovedNotification),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.unlock,
                    conditions=[activity_spots_left],
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.expire,
                    conditions=[activity_will_be_expired],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.auto_remove,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.unlock,
                    conditions=[activity_spots_left],
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.expire,
                    conditions=[activity_will_be_expired],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.fail,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.unlock,
                    conditions=[activity_spots_left],
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.expire,
                    conditions=[activity_will_be_expired],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.reject,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.unlock,
                    conditions=[activity_spots_left],
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.expire,
                    conditions=[activity_will_be_expired],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.unlock,
                    conditions=[activity_spots_left],
                ),
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.expire,
                    conditions=[activity_will_be_expired],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.schedule,
            effects=[
                NotificationEffect(UserScheduledNotification),
                RelatedTransitionEffect(
                    'contributions',
                    ContributionStateMachine.reset,
                ),
                TransitionEffect(
                    ScheduleParticipantStateMachine.succeed,
                    conditions=[slot_is_finished],
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.unschedule,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    ContributionStateMachine.reset,
                ),
            ],
        ),
        ModelChangedTrigger(
            "slot_id",
            effects=[
                TransitionEffect(
                    ScheduleParticipantStateMachine.schedule, conditions=[has_scheduled_slot]
                ),
                TransitionEffect(
                    ScheduleParticipantStateMachine.unschedule, conditions=[has_no_slot]
                ),
            ],
        ),
    ]


@register(TeamScheduleParticipant)
class TeamScheduleParticipantTriggers(ContributorTriggers):
    def has_slot(effect):
        """Has a slot"""
        return effect.instance.slot.status == "scheduled"

    def team_is_accepted(effect):
        """Team is accepted"""
        return effect.instance.team_member.team.status != "new"

    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            TeamScheduleParticipantStateMachine.initiate,
            effects=[
                CreateScheduleContributionEffect,
                TransitionEffect(
                    TeamScheduleParticipantStateMachine.schedule, conditions=[has_slot]
                ),
                TransitionEffect(
                    TeamScheduleParticipantStateMachine.accept,
                    conditions=[team_is_accepted],
                ),
            ],
        ),
        TransitionTrigger(
            TeamScheduleParticipantStateMachine.reapply,
            effects=[
                TransitionEffect(
                    TeamScheduleParticipantStateMachine.schedule, conditions=[has_slot]
                ),
                TransitionEffect(
                    TeamScheduleParticipantStateMachine.accept,
                    conditions=[team_is_accepted],
                ),
                RelatedTransitionEffect(
                    "team_member",
                    TeamMemberStateMachine.reapply,
                )
            ],
        ),
        TransitionTrigger(
            TeamScheduleParticipantStateMachine.readd,
            effects=[
                TransitionEffect(
                    TeamScheduleParticipantStateMachine.schedule, conditions=[has_slot]
                ),
                TransitionEffect(
                    TeamScheduleParticipantStateMachine.accept,
                    conditions=[team_is_accepted],
                ),
            ],
        ),
        TransitionTrigger(
            TeamScheduleParticipantStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.succeed,
                ),
                RelatedTransitionEffect(
                    "activity",
                    RegistrationActivityStateMachine.succeed,
                    conditions=[activity_is_expired],
                ),
            ],
        ),
        TransitionTrigger(
            TeamScheduleParticipantStateMachine.reset,
            effects=[
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.reset,
                ),
            ],
        ),
        TransitionTrigger(
            TeamScheduleParticipantStateMachine.unschedule,
            effects=[
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.reset,
                ),
            ],
        ),
        TransitionTrigger(
            TeamScheduleParticipantStateMachine.withdraw,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
            ],
        ),
        TransitionTrigger(
            TeamScheduleParticipantStateMachine.reapply,
            effects=[
                FollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.reset,
                ),
            ],
        ),
        TransitionTrigger(
            TeamScheduleParticipantStateMachine.readd,
            effects=[
                FollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.reset,
                ),
            ],
        ),
        TransitionTrigger(
            TeamScheduleParticipantStateMachine.remove,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.expire,
                    conditions=[activity_will_be_expired],
                ),
            ],
        ),
        TransitionTrigger(
            TeamScheduleParticipantStateMachine.auto_remove,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.expire,
                    conditions=[activity_will_be_expired],
                ),
            ],
        ),
        TransitionTrigger(
            TeamScheduleParticipantStateMachine.fail,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.expire,
                    conditions=[activity_will_be_expired],
                ),
            ],
        ),
        TransitionTrigger(
            TeamScheduleParticipantStateMachine.reject,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.expire,
                    conditions=[activity_will_be_expired],
                ),
            ],
        ),
    ]


@register(DateParticipant)
class DateParticipantTriggers(RegistrationParticipantTriggers):

    def participant_slot_is_finished(effect):
        """
        Slot end date/time has passed
        """
        if effect.instance.slot:
            return effect.instance.slot.status == 'finished'

    def applicant_is_accepted(effect):
        return effect.instance.registration and effect.instance.registration.status == 'accepted'

    def is_participant(effect):
        if 'user' not in effect.options:
            return False
        return effect.instance.user == effect.options['user']

    def participant_slot_will_be_full(effect):
        """
        the slot will be filled
        """
        participant_count = effect.instance.slot.participants.filter(
            status="accepted",
            registration__status="accepted"
        ).count()

        if (
                effect.instance.slot.capacity and
                effect.instance.status == 'accepted' and
                participant_count + 1 >= effect.instance.slot.capacity
        ):
            return True
        return False

    def participant_slot_will_be_not_full(effect):
        """
        the slot will be unfilled
        """
        # Handle case where instance might be in deletion state
        if not hasattr(effect.instance, 'slot') or not effect.instance.slot:
            return False

        participant_count = effect.instance.slot.participants.filter(
            status='accepted',
            registration__status='accepted'
        ).count()
        if effect.instance.slot.capacity and participant_count - 1 < effect.instance.slot.capacity:
            return True
        return False

    def is_not_self(self):
        "Participant is created by other user"
        user = self.options.get('user')

        return user and self.instance.user != user

    def registration_is_accepted(effect):
        """Review needed"""
        return (
            effect.instance.registration
            and effect.instance.registration.status == "accepted"
        )

    def registration_is_withdrawn(effect):
        """Registration is withdrawn"""
        return (
            effect.instance.registration
            and effect.instance.registration.status == "withdrawn"
        )

    def review_disabled(effect):
        """Review not needed"""
        return not effect.instance.activity.review

    def slot_is_in_future(effect):
        """Check if the slot is in the future."""
        return effect.instance.slot.start > now()

    def slot_is_in_past(effect):
        """Check if the slot is in the past."""
        return effect.instance.slot.start < now()

    def no_active_participation(effect):
        """Related registration has no active participants"""
        # Handle case where instance might be in deletion state
        if not hasattr(effect.instance, 'registration') or not effect.instance.registration:
            return False

        return not effect.instance.registration.participants.exclude(
            id=effect.instance.id
        ).filter(
            status__in=['accepted', 'succeeded', 'new']
        ).exists()

    triggers = [
        TransitionTrigger(
            DateParticipantStateMachine.initiate,
            effects=[
                CreateDateRegistrationEffect,
                CreateSlotTimeContributionEffect,
                TransitionEffect(
                    DateParticipantStateMachine.add,
                    conditions=[is_not_self],
                ),
                TransitionEffect(
                    DateParticipantStateMachine.accept,
                    conditions=[review_disabled],
                ),
                TransitionEffect(
                    DateParticipantStateMachine.accept,
                    conditions=[
                        is_participant,
                        registration_is_accepted
                    ],
                ),
                RelatedTransitionEffect(
                    'slot',
                    DateActivitySlotStateMachine.lock,
                    conditions=[participant_slot_will_be_full]
                ),
                NotificationEffect(
                    ManagerSlotParticipantRegisteredNotification,
                    conditions=[
                        review_disabled,
                        is_participant
                    ]
                ),
                NotificationEffect(
                    ParticipantSlotParticipantRegisteredNotification,
                    conditions=[
                        review_disabled,
                        is_participant
                    ]
                ),
            ]
        ),

        TransitionTrigger(
            DateParticipantStateMachine.remove,
            effects=[
                CheckPreparationTimeContributionEffect,
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    'slot',
                    DateActivitySlotStateMachine.unlock,
                    conditions=[participant_slot_will_be_not_full]
                ),
                NotificationEffect(ParticipantChangedNotification),
                SlotParticipantUnFollowActivityEffect,
            ],
        ),

        TransitionTrigger(
            DateParticipantStateMachine.accept,
            effects=[
                TransitionEffect(
                    RegistrationParticipantStateMachine.succeed,
                    conditions=[participant_slot_is_finished]

                ),
                CheckPreparationTimeContributionEffect,
                RelatedTransitionEffect(
                    'slot',
                    DateActivitySlotStateMachine.lock,
                    conditions=[participant_slot_will_be_full]
                ),
                FollowActivityEffect,
            ],
        ),

        TransitionTrigger(
            DateParticipantStateMachine.add,
            effects=[
                TransitionEffect(
                    RegistrationParticipantStateMachine.succeed,
                    conditions=[participant_slot_is_finished]

                ),
                CheckPreparationTimeContributionEffect,
                FollowActivityEffect,
            ],
        ),

        TransitionTrigger(
            DateParticipantStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    DateStateMachine.succeed,
                    conditions=[activity_is_expired]
                ),
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.succeed,
                ),
            ],
        ),

        TransitionTrigger(
            DateParticipantStateMachine.reject,
            effects=[
                CheckPreparationTimeContributionEffect,
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    'slot',
                    DateActivitySlotStateMachine.unlock,
                    conditions=[participant_slot_will_be_not_full]
                ),
                SlotParticipantUnFollowActivityEffect,
            ],
        ),

        TransitionTrigger(
            DateParticipantStateMachine.withdraw,
            effects=[
                CheckPreparationTimeContributionEffect,
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    'slot',
                    DateActivitySlotStateMachine.unlock,
                    conditions=[participant_slot_will_be_not_full]
                ),
                RelatedTransitionEffect(
                    'registration',
                    RegistrationStateMachine.withdraw,
                    conditions=[no_active_participation]
                ),
                NotificationEffect(
                    ManagerSlotParticipantWithdrewNotification,
                ),
                NotificationEffect(
                    UserDateParticipantWithdrewNotification
                ),
                SlotParticipantUnFollowActivityEffect,
            ],
        ),
        TransitionTrigger(
            DateParticipantStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
                ),
            ]
        ),

        TransitionTrigger(
            DateParticipantStateMachine.reapply,
            effects=[
                CheckPreparationTimeContributionEffect,
                TransitionEffect(
                    DateParticipantStateMachine.accept,
                    conditions=[registration_is_accepted]
                ),
                RelatedTransitionEffect(
                    'registration',
                    RegistrationStateMachine.restore,
                    conditions=[registration_is_withdrawn]
                ),
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.reset,
                ),
                RelatedTransitionEffect(
                    'slot',
                    DateActivitySlotStateMachine.lock,
                    conditions=[participant_slot_will_be_full]
                ),
                RelatedTransitionEffect(
                    'slot',
                    DateActivitySlotStateMachine.lock,
                    conditions=[participant_slot_will_be_full]
                ),
                NotificationEffect(ParticipantChangedNotification),
                NotificationEffect(
                    ManagerSlotParticipantRegisteredNotification,
                    conditions=[applicant_is_accepted]
                ),
                FollowActivityEffect,
            ],
        ),

        TransitionTrigger(
            DateParticipantStateMachine.readd,
            effects=[
                CheckPreparationTimeContributionEffect,
                TransitionEffect(
                    DateParticipantStateMachine.accept,
                    conditions=[registration_is_accepted]
                ),
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.reset,
                ),
                RelatedTransitionEffect(
                    'slot',
                    DateActivitySlotStateMachine.lock,
                    conditions=[participant_slot_will_be_full]
                ),
                RelatedTransitionEffect(
                    'slot',
                    DateActivitySlotStateMachine.lock,
                    conditions=[participant_slot_will_be_full]
                ),
                NotificationEffect(ParticipantChangedNotification),
                NotificationEffect(
                    ManagerSlotParticipantRegisteredNotification,
                    conditions=[applicant_is_accepted]
                ),
                FollowActivityEffect,
            ],
        ),
        TransitionTrigger(
            DateParticipantStateMachine.restore,
            effects=[
                CheckPreparationTimeContributionEffect,
                TransitionEffect(
                    DateParticipantStateMachine.accept,
                    conditions=[registration_is_accepted]
                ),
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.reset,
                    conditions=[
                        slot_is_in_future
                    ]
                ),
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.succeed,
                    conditions=[
                        slot_is_in_past
                    ]
                ),
                RelatedTransitionEffect(
                    'slot',
                    DateActivitySlotStateMachine.lock,
                    conditions=[participant_slot_will_be_full]
                ),
                FollowActivityEffect,
            ],
        ),
        ModelDeletedTrigger(
            effects=[
                RelatedTransitionEffect(
                    'slot',
                    DateActivitySlotStateMachine.unlock,
                    conditions=[participant_slot_will_be_not_full]
                ),
                DeleteRegistrationEffect
            ]
        )
    ]


@register(RegisteredDateParticipant)
class RegisteredDateParticipantTriggers(ContributorTriggers):

    def activity_is_succeeded(effect):
        """Slot has status finished"""
        return effect.instance.activity and effect.instance.activity.status == "succeeded"

    def activity_is_not_succeeded(effect):
        """Slot has status finished"""
        return effect.instance.activity and effect.instance.activity.status != "succeeded"

    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            RegisteredDateParticipantStateMachine.initiate,
            effects=[
                FollowActivityEffect,
                CreateRegisteredTimeContributionEffect,
                TransitionEffect(
                    RegisteredDateParticipantStateMachine.succeed,
                    conditions=[activity_is_succeeded],
                ),
            ],
        ),
        TransitionTrigger(
            RegisteredDateParticipantStateMachine.succeed,
            effects=[
                NotificationEffect(
                    RegisteredActivityParticipantAddedNotification,
                ),
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.succeed,
                ),
                RelatedTransitionEffect(
                    'activity',
                    RegisteredDateActivityStateMachine,
                    conditions=[activity_is_expired],
                )
            ]
        ),
        TransitionTrigger(
            RegisteredDateParticipantStateMachine.readd,
            effects=[
                TransitionEffect(
                    RegisteredDateParticipantStateMachine.succeed,
                    conditions=[
                        activity_is_succeeded
                    ]
                ),
                RelatedTransitionEffect(
                    'activity',
                    RegisteredDateActivityStateMachine.succeed,
                    conditions=[activity_is_expired],
                )
            ]
        ),
        TransitionTrigger(
            RegisteredDateParticipantStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
                ),
                RelatedTransitionEffect(
                    'activity',
                    RegisteredDateActivityStateMachine.expire,
                    conditions=[activity_will_be_expired],
                )

            ]
        ),
        TransitionTrigger(
            RegisteredDateParticipantStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
                ),
            ]
        ),
        TransitionTrigger(
            RegisteredDateParticipantStateMachine.restore,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.reset,
                ),
                RelatedTransitionEffect(
                    'activity',
                    RegisteredDateActivityStateMachine.succeed,
                    conditions=[activity_is_expired],
                )
            ]
        ),
    ]
