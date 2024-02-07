from bluebottle.fsm.triggers import (
    register, TransitionTrigger, TriggerManager
)
from bluebottle.notifications.effects import NotificationEffect
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
        return effect.instance.activity.review

    triggers = [
        TransitionTrigger(
            RegistrationStateMachine.initiate,
            effects=[
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


@register(RegistrationTriggers)
class DeadlineRegistrationTriggers(TriggerManager):
    pass
