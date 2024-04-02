from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import TransitionTrigger, TriggerManager, register
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects.registration import (
    CreateInitialPeriodicParticipantEffect,
    CreateParticipantEffect,
)
from bluebottle.time_based.models import (
    DeadlineRegistration,
    PeriodicRegistration,
    ScheduleRegistration,
)
from bluebottle.time_based.notifications.registrations import (
    ManagerRegistrationCreatedNotification,
    ManagerRegistrationCreatedReviewNotification,
    UserAppliedNotification,
    UserJoinedNotification,
    UserRegistrationAcceptedNotification,
    UserRegistrationRejectedNotification,
    UserRegistrationRestartedNotification,
    UserRegistrationStoppedNotification,
)
from bluebottle.time_based.states import (
    DeadlineParticipantStateMachine,
    RegistrationStateMachine,
)
from bluebottle.time_based.states.participants import (
    PeriodicParticipantStateMachine,
    RegistrationParticipantStateMachine,
    ScheduleParticipantStateMachine,
)
from bluebottle.time_based.states.registrations import (
    PeriodicRegistrationStateMachine,
    ScheduleRegistrationStateMachine,
)
from bluebottle.time_based.states.states import PeriodicActivityStateMachine


class RegistrationTriggers(TriggerManager):

    def review_needed(effect):
        """ Review needed """
        return effect.instance.activity.review

    def no_review_needed(effect):
        """ No review needed """
        return not effect.instance.activity.review

    triggers = [
        TransitionTrigger(
            RegistrationStateMachine.initiate,
            effects=[
                TransitionEffect(
                    RegistrationStateMachine.auto_accept,
                    conditions=[
                        no_review_needed
                    ]
                ),
                NotificationEffect(
                    ManagerRegistrationCreatedReviewNotification,
                    conditions=[
                        review_needed
                    ]
                ),
                NotificationEffect(
                    UserAppliedNotification,
                    conditions=[
                        review_needed
                    ]
                ),
                NotificationEffect(
                    ManagerRegistrationCreatedNotification,
                    conditions=[
                        no_review_needed
                    ]
                ),
                NotificationEffect(
                    UserJoinedNotification,
                    conditions=[
                        no_review_needed
                    ]
                ),
            ]
        ),
        TransitionTrigger(
            RegistrationStateMachine.accept,
            effects=[
                NotificationEffect(
                    UserRegistrationAcceptedNotification,
                ),
            ]
        ),
        TransitionTrigger(
            RegistrationStateMachine.reject,
            effects=[
                NotificationEffect(
                    UserRegistrationRejectedNotification,
                ),
                RelatedTransitionEffect(
                    'participants',
                    RegistrationParticipantStateMachine.reject,
                ),
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
            ]
        ),
        TransitionTrigger(
            RegistrationStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    DeadlineParticipantStateMachine.accept,
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
    ]


@register(PeriodicRegistration)
class PeriodicRegistrationTriggers(RegistrationTriggers):
    def activity_no_spots_left(effect):
        """Activity has spots available after this effect"""
        if not effect.instance.activity.capacity:
            return False
        accepted = effect.instance.activity.registrations.filter(status="accepted").count()
        return effect.instance.activity.capacity <= accepted + 1

    def activity_spots_left(effect):
        """Activity has spots available after this effect"""
        if not effect.instance.activity.capacity:
            return True
        accepted = effect.instance.activity.registrations.filter(status="accepted").count()
        return effect.instance.activity.capacity > accepted - 1

    triggers = RegistrationTriggers.triggers + [
        TransitionTrigger(
            PeriodicRegistrationStateMachine.auto_accept,
            effects=[
                RelatedTransitionEffect(
                    "activity",
                    PeriodicActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
                CreateInitialPeriodicParticipantEffect,
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
                CreateInitialPeriodicParticipantEffect,
            ],
        ),
        TransitionTrigger(
            PeriodicRegistrationStateMachine.reject,
            effects=[
                RelatedTransitionEffect(
                    "activity",
                    PeriodicActivityStateMachine.unlock,
                    conditions=[activity_spots_left],
                )
            ],
        ),
        TransitionTrigger(
            PeriodicRegistrationStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    PeriodicParticipantStateMachine.withdraw,
                ),
                RelatedTransitionEffect(
                    "activity",
                    PeriodicActivityStateMachine.unlock,
                    conditions=[activity_spots_left],
                ),
            ],
        ),
        TransitionTrigger(
            PeriodicRegistrationStateMachine.reapply,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    PeriodicParticipantStateMachine.restore,
                ),
                RelatedTransitionEffect(
                    "activity",
                    PeriodicActivityStateMachine.lock,
                    conditions=[activity_no_spots_left],
                ),
            ],
        ),
        TransitionTrigger(
            PeriodicRegistrationStateMachine.start,
            effects=[NotificationEffect(UserRegistrationRestartedNotification)],
        ),
        TransitionTrigger(
            PeriodicRegistrationStateMachine.stop,
            effects=[NotificationEffect(UserRegistrationStoppedNotification)],
        ),
    ]


@register(ScheduleRegistration)
class ScheduleRegistrationTriggers(RegistrationTriggers):
    triggers = RegistrationTriggers.triggers + [
        TransitionTrigger(
            RegistrationStateMachine.initiate,
            effects=[
                CreateParticipantEffect,
            ],
        ),
        TransitionTrigger(
            RegistrationStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    ScheduleParticipantStateMachine.accept,
                ),
            ],
        ),
    ]
