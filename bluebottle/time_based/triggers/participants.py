from bluebottle.activities.states import ContributionStateMachine
from bluebottle.activities.triggers import ContributorTriggers
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
from bluebottle.time_based.effects.participant import (
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
    PeriodicParticipant,
    ScheduleParticipant,
)
from bluebottle.time_based.notifications.participants import (
    ManagerParticipantRemovedNotification,
    UserParticipantRemovedNotification,
    UserParticipantWithdrewNotification,
    ManagerParticipantWithdrewNotification,
)
from bluebottle.time_based.states import (
    ParticipantStateMachine,
    DeadlineParticipantStateMachine,
    DeadlineActivityStateMachine,
    RegistrationActivityStateMachine,
    PeriodicParticipantStateMachine,
    RegistrationParticipantStateMachine,
)
from bluebottle.time_based.states.participants import ScheduleParticipantStateMachine
from bluebottle.time_based.states.states import ScheduleActivityStateMachine


class ParticipantTriggers(ContributorTriggers):
    def activity_is_expired(effect):
        """Activity is expired"""
        return effect.instance.activity.status == "expired"

    triggers = ContributorTriggers.triggers + []


@register(DeadlineParticipant)
class DeadlineParticipantTriggers(ParticipantTriggers):
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

    triggers = ParticipantTriggers.triggers + []


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
                ),
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
                ),
            ],
        ),
    ]


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

    def has_no_slot(effect):
        """Has no assigned slot"""
        return not effect.instance.slot

    triggers = ParticipantTriggers.triggers + []
