from bluebottle.time_based.states import ParticipantStateMachine


@register(Application)
class ApplicationTriggers(TriggerManager):
    triggers = ActivityTriggers.triggers + [
        TransitionTrigger(
            ApplicationStateMachine.initiate,
            effects=[
                TransitionEffect(ApplicaStateMachine.automatically_accept),
            ]
        ),
        TransitionTrigger(
            ApplicationStateMachine.accept,
            effects=[
                NotificationEffect(ApplicationAcceptedNotification),
                RelatedTransitionEffect('participants', ParticipantStateMachine.accept),
            ]
        ),
        TransitionTrigger(
            ApplicationStateMachine.automatically_accept,
            effects=[
                RelatedTransitionEffect('participants', ParticipantStateMachine.accept),
            ]
        ),
        TransitionTrigger(
            ApplicationStateMachine.reject,
            effects=[
                NotificationEffect(ApplicationRejectedNotification),
                RelatedTransitionEffect('participants', ParticipantStateMachine.reject),
            ]
        ),
    ]



