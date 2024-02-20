from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    register, TransitionTrigger, TriggerManager
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects.registration import CreateDeadlineParticipantEffect
from bluebottle.time_based.models import DeadlineRegistration
from bluebottle.time_based.notifications.registrations import (
    ManagerRegistrationCreatedReviewNotification, ManagerRegistrationCreatedNotification,
    UserRegistrationAcceptedNotification, UserRegistrationRejectedNotification,
    UserAppliedNotification, UserJoinedNotification
)
from bluebottle.time_based.states import (
    RegistrationStateMachine, ParticipantStateMachine, DeadlineParticipantStateMachine
)


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
                CreateDeadlineParticipantEffect,
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
                RelatedTransitionEffect(
                    'participants',
                    DeadlineParticipantStateMachine.accept,
                ),
            ]
        ),
        TransitionTrigger(
            RegistrationStateMachine.auto_accept,
            effects=[
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
                    ParticipantStateMachine.reject,
                ),
            ]
        )

    ]


@register(DeadlineRegistration)
class DeadlineRegistrationTriggers(RegistrationTriggers):
    pass
