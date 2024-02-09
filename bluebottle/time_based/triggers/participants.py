from bluebottle.activities.states import ContributionStateMachine
from bluebottle.activities.triggers import (
    ContributorTriggers
)
from bluebottle.follow.effects import FollowActivityEffect
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    TransitionTrigger, register
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects import CreatePreparationTimeContributionEffect
from bluebottle.time_based.effects.participant import CreateTimeContributionEffect, CreateRegistrationEffect
from bluebottle.time_based.messages import ManagerParticipantAddedOwnerNotification, ParticipantAddedNotification
from bluebottle.time_based.models import DeadlineParticipant
from bluebottle.time_based.states import (
    ParticipantStateMachine, DeadlineParticipantStateMachine
)


@register(DeadlineParticipant)
class DeadlineParticipantTriggers(ContributorTriggers):
    def review_needed(effect):
        """ Review needed """
        return effect.instance.activity.review

    def no_review_needed(effect):
        """ No review needed """
        return not effect.instance.activity.review

    def is_admin(effect):
        """ Is admin """
        user = effect.options.get('user', None)
        return user and (user.is_staff or user.is_superuser)

    triggers = [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                FollowActivityEffect,
                CreatePreparationTimeContributionEffect,
                CreateTimeContributionEffect,
                CreateRegistrationEffect,
                TransitionEffect(
                    ParticipantStateMachine.accept,
                    conditions=[
                        no_review_needed
                    ]
                ),
                TransitionEffect(
                    ParticipantStateMachine.add,
                    conditions=[
                        is_admin
                    ]
                ),
            ]
        ),
        TransitionTrigger(
            ParticipantStateMachine.accept,
            effects=[
                TransitionEffect(
                    DeadlineParticipantStateMachine.succeed,
                ),
            ]
        ),
        TransitionTrigger(
            ParticipantStateMachine.add,
            effects=[
                CreateRegistrationEffect,
                NotificationEffect(ManagerParticipantAddedOwnerNotification),
                NotificationEffect(ParticipantAddedNotification),
                TransitionEffect(
                    DeadlineParticipantStateMachine.succeed,
                ),
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    ContributionStateMachine.succeed,
                ),
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    ContributionStateMachine.fail,
                ),
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    ContributionStateMachine.fail,
                ),
            ]
        ),
        TransitionTrigger(
            DeadlineParticipantStateMachine.cancelled,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    ContributionStateMachine.fail,
                ),
            ]
        ),
    ]
