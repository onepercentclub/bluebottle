from bluebottle.activities.states import ContributionStateMachine
from bluebottle.activities.triggers import (
    ContributorTriggers
)
from bluebottle.follow.effects import FollowActivityEffect, UnFollowActivityEffect
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    TransitionTrigger, register
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects import CreatePreparationTimeContributionEffect
from bluebottle.time_based.effects.participant import (
    CreateTimeContributionEffect,
    CreateRegistrationEffect,
)
from bluebottle.time_based.messages import (
    ManagerParticipantAddedOwnerNotification,
    ParticipantAddedNotification,
)
from bluebottle.time_based.models import (
    DeadlineParticipant,
    PeriodicParticipant,
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
)


class ParticipantTriggers(ContributorTriggers):
    def activity_is_expired(effect):
        """Activity is expired"""
        return effect.instance.activity.status == "expired"

    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                FollowActivityEffect,
                CreatePreparationTimeContributionEffect,
                CreateTimeContributionEffect,
            ],
        ),
        TransitionTrigger(
            ParticipantStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.succeed,
                ),
                RelatedTransitionEffect(
                    "activity",
                    DeadlineActivityStateMachine.succeed,
                    conditions=[activity_is_expired],
                ),
            ],
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.reject,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
                ),
            ],
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.cancelled,
            effects=[
                UnFollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.fail,
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
                FollowActivityEffect,
                RelatedTransitionEffect(
                    "contributions",
                    ContributionStateMachine.succeed,
                ),
                RelatedTransitionEffect(
                    "activity",
                    DeadlineActivityStateMachine.succeed,
                    conditions=[ParticipantTriggers.activity_is_expired],
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
                FollowActivityEffect,
                RelatedTransitionEffect(
                    'activity',
                    DeadlineActivityStateMachine.lock,
                    conditions=[
                        activity_no_spots_left
                    ]
                ),

                RelatedTransitionEffect(
                    'contributions',
                    ContributionStateMachine.succeed,
                ),
                RelatedTransitionEffect(
                    'activity',
                    DeadlineActivityStateMachine.succeed,
                    conditions=[ParticipantTriggers.activity_is_expired],
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

                UnFollowActivityEffect,
                NotificationEffect(UserParticipantWithdrewNotification),
                NotificationEffect(ManagerParticipantWithdrewNotification),
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
            DeadlineParticipantStateMachine.reapply,
            effects=[
                FollowActivityEffect,
                RelatedTransitionEffect(
                    'contributions',
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
            DeadlineParticipantStateMachine.remove,
            effects=[
                UnFollowActivityEffect,
                NotificationEffect(UserParticipantRemovedNotification),
                NotificationEffect(ManagerParticipantRemovedNotification),
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
    triggers = ParticipantTriggers.triggers + []
