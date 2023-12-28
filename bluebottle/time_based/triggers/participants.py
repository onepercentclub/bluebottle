
from bluebottle.activities.states import ContributionStateMachine
from bluebottle.deeds.messages import ParticipantJoinedNotification
from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.fsm.triggers import TransitionTrigger
from bluebottle.time_based.messages import ParticipantRejectedNotification, ParticipantWithdrewNotification
from bluebottle.time_based.states import ParticipantStateMachine


class ParticipantTriggers(TriggerManager):
    triggers = ActivityTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.accept,
            effects=[
                RelatedTransitionEffect('contributions', ContributionStateMachine.succeed, conditions=[slot_is_finished]),
                RelatedTransitionEffect('contributions', ContributionStateMachine.reset, conditions=[slot_is_not_finished]),
            ]
        ),
        TransitionTrigger(
            ParticipantStateMachine.accept,
            effects=[
                RelatedTransitionEffect('contributions', ContributionStateMachine.succeed, conditions=[slot_is_finished]),
                RelatedTransitionEffect('contributions', ContributionStateMachine.reset, conditions=[slot_is_not_finished]),
            ]
        ),
        TransitionTrigger(
            ParticipantStateMachine.reject,
            effects=[
                RelatedTransitionEffect('contributions', ContributionStateMachine.fail),
            ]
        ),
        TransitionTrigger(
            ParticipantStateMachine.withdraw,
            effects=[
                NotificationEffect(ParticipantWithdrewNotification),
                RelatedTransitionEffect('contributions', ContributionStateMachine.fail),
            ]
        ),
        TransitionTrigger(
            ParticipantStateMachine.reapply,
            effects=[
                NotificationEffect(ParticipantReAppliedNotification),
                RelatedTransitionEffect('contributions', ContributionStateMachine.reset),
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.reject,
            effects=[
                NotificationEffect(ParticipantRejectedNotification),
                RelatedTransitionEffect('contributions', ContributionStateMachine.fail),
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.reaccept,
            effects=[
                NotificationEffect(ParticipantReAcceptedNotification),
                RelatedTransitionEffect('contributions', ContributionStateMachine.reset),
            ]
        ),
    ]


@register(PredefinedParticipant)
class PredefinedParticipantTriggers(ParticipantTriggers):
    triggers = ParticipantTriggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                NotificationEffect(PredefinedParticipantJoinedNotification, conditions=[application_is_accepted]),
            ]
        ),
    ]


@register(FreeParticipant)
class PredefinedParticipantTriggers(ParticipantTriggers):
    triggers = ParticipantTriggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                AssigntoNewSlot(), #TODO maybe not use slots for free participants
                NotificationEffect(FreeParticipantJoinedNotification, conditions=[application_is_accepted]),
                TransitionTrigger(
                    FreeParticipantStateMachine.automatically_succeed
                ),
                RelatedTransitionEffect(
                    'activity', ActivityStateMachine.lock, conditions=[activity_is_full] 
                )
            ]
        ),
    ]

@register(TBAParticipant)
class TBAParticipantTriggers(ParticipantTriggers):
    triggers = ParticipantTriggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            AssignToEmptySlot(),
            effects=[
                NotificationEffect(TBAParticipantJoinedNotification, conditions=[application_is_accepted]),
                RelatedTransitionEffect(
                    'activity', ActivityStateMachine.lock, conditions=[activity_is_full] 
                )
            ]
        ),
    ]

@register(PeriodicParticipant)
class PeriodicParticipantTriggers(ParticipantTriggers):
    triggers = ParticipantTriggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                AssignToCurrentSlot(),
                RelatedTransitionEffect(
                    'activity', ActivityStateMachine.lock, conditions=[activity_is_full] 
                )
            ]
        ),
    ]
