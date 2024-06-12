from django.utils.timezone import now

from bluebottle.activities.states import ContributionStateMachine
from bluebottle.activities.triggers import (
    ContributorTriggers
)
from bluebottle.follow.effects import FollowActivityEffect, UnFollowActivityEffect
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    TransitionTrigger,
    register,
    ModelDeletedTrigger,
    ModelChangedTrigger,
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects import CreatePreparationTimeContributionEffect
from bluebottle.time_based.effects.effects import (
    CreateSchedulePreparationTimeContributionEffect,
)
from bluebottle.time_based.effects.participants import (
    CreateScheduleContributionEffect,
    CreateTimeContributionEffect,
    CreateRegistrationEffect,
    CreatePeriodicPreparationTimeContributionEffect,
)
from bluebottle.time_based.messages import (
    ManagerParticipantAddedOwnerNotification,
    ParticipantAddedNotification,
)
from bluebottle.time_based.models import (
    DeadlineParticipant,
    PeriodicParticipant, ScheduleParticipant, TeamScheduleParticipant,
)
from bluebottle.time_based.notifications.participants import (
    ManagerParticipantRemovedNotification,
    UserParticipantRemovedNotification,
    UserParticipantWithdrewNotification,
    ManagerParticipantWithdrewNotification, UserScheduledNotification,
)
from bluebottle.time_based.states import (
    ParticipantStateMachine,
    DeadlineParticipantStateMachine,
    DeadlineActivityStateMachine,
    RegistrationActivityStateMachine,
    PeriodicParticipantStateMachine,
    RegistrationParticipantStateMachine,
    ScheduleParticipantStateMachine,
    ScheduleActivityStateMachine,
    TeamScheduleParticipantStateMachine,
)


class ParticipantTriggers(ContributorTriggers):
    def activity_is_expired(effect):
        """Activity is expired"""
        return effect.instance.activity.status == "expired"

    triggers = ContributorTriggers.triggers + [
        ModelDeletedTrigger(

        ),
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
                    DeadlineActivityStateMachine.succeed,
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
            ],
        ),
        TransitionTrigger(
            RegistrationParticipantStateMachine.readd,
            effects=[
                FollowActivityEffect,
                RelatedTransitionEffect(
                    "activity",
                    DeadlineActivityStateMachine.succeed,
                    conditions=[activity_is_expired],
                ),
            ],
        ),
    ]


@register(DeadlineParticipant)
class DeadlineParticipantTriggers(ParticipantTriggers):
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

    triggers = ParticipantTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                CreateRegistrationEffect,
                CreateTimeContributionEffect,
                CreatePreparationTimeContributionEffect,
                TransitionEffect(
                    DeadlineParticipantStateMachine.add,
                    conditions=[
                        is_admin
                    ]
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
                NotificationEffect(ManagerParticipantAddedOwnerNotification),
                NotificationEffect(ParticipantAddedNotification),
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
            DeadlineParticipantStateMachine.readd,
            effects=[
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
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.succeed,
                ),
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
            RegistrationParticipantStateMachine.readd,
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
            DeadlineParticipantStateMachine.remove,
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
class PeriodicParticipantTriggers(ParticipantTriggers):
    def slot_is_finished(effect):
        """Slot has status finished"""
        return effect.instance.slot.status == "finished"

    def registration_is_accepted(effect):
        """Review needed"""
        return (
            effect.instance.registration
            and effect.instance.registration.status == "accepted"
        )

    triggers = ParticipantTriggers.triggers + [
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
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.succeed,
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
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.succeed,
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
                    ContributionStateMachine.succeed,
                ),
                TransitionEffect(
                    PeriodicParticipantStateMachine.succeed,
                    conditions=[slot_is_finished],
                )
            ],
        ),
    ]


@register(ScheduleParticipant)
class ScheduleParticipantTriggers(ParticipantTriggers):
    def registration_is_accepted(effect):
        """Review needed"""
        return (
            effect.instance.registration
            and effect.instance.registration.status == "accepted"
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

    def has_slot(effect):
        """Has assigned slot"""
        return effect.instance.slot

    def slot_is_finished(effect):
        """Has assigned slot"""
        return effect.instance.slot and effect.instance.slot.end < now()

    def has_no_slot(effect):
        """Has no assigned slot"""
        return not effect.instance.slot

    triggers = ParticipantTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                CreateScheduleContributionEffect,
                CreateRegistrationEffect,
                TransitionEffect(
                    ScheduleParticipantStateMachine.add, conditions=[is_admin]
                ),
                TransitionEffect(
                    ScheduleParticipantStateMachine.accept,
                    conditions=[registration_is_accepted],
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
                    ScheduleParticipantStateMachine.schedule, conditions=[has_slot]
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.add,
            effects=[
                CreateRegistrationEffect,
                NotificationEffect(ManagerParticipantAddedOwnerNotification),
                NotificationEffect(ParticipantAddedNotification),
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
            DeadlineParticipantStateMachine.restore,
            effects=[
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
                        registration_is_accepted,
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
                        registration_is_accepted,
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
                )
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.cancelled,
            effects=[
                RelatedTransitionEffect(
                    "activity",
                    ScheduleActivityStateMachine.unlock,
                    conditions=[activity_spots_left],
                )
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.schedule,
            effects=[
                NotificationEffect(UserScheduledNotification),
                CreateSchedulePreparationTimeContributionEffect,
                CreateScheduleContributionEffect,
                TransitionEffect(
                    ScheduleParticipantStateMachine.succeed,
                    conditions=[slot_is_finished],
                ),
            ],
        ),
        ModelChangedTrigger(
            "slot_id",
            effects=[
                TransitionEffect(
                    ScheduleParticipantStateMachine.schedule, conditions=[has_slot]
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
            ScheduleParticipantStateMachine.initiate,
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
            ScheduleParticipantStateMachine.reapply,
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
            ScheduleParticipantStateMachine.readd,
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
            ScheduleParticipantStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.succeed,
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
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.reapply,
            effects=[
                FollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.reset,
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleParticipantStateMachine.readd,
            effects=[
                FollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.reset,
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
            ],
        ),
    ]
