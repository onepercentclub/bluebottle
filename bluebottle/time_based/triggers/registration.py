from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.triggers import (
    register, TransitionTrigger, TriggerManager
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects.registration import CreateDeadlineParticipantEffect
from bluebottle.time_based.models import DeadlineRegistration
from bluebottle.time_based.notifications.registration import ManagerRegistrationCreatedReviewNotification, \
    ManagerRegistrationCreatedNotification
from bluebottle.time_based.states import (
    RegistrationStateMachine
)


class RegistrationTriggers(TriggerManager):

    def review_needed(effect):
        """
        Review needed
        """
        return effect.instance.activity.review

    def no_review_needed(effect):
        """
        No review needed
        """
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
                    ManagerRegistrationCreatedNotification,
                    conditions=[
                        no_review_needed
                    ]
                ),
            ]
        )
    ]


@register(DeadlineRegistration)
class DeadlineRegistrationTriggers(RegistrationTriggers):
    pass
