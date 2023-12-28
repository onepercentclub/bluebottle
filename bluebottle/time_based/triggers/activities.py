
class TimeBasedTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [
        TransitionTrigger(
            TimeBasedStateMachine.succeed,
            effects=[
                NotificationEffect(ActivitySucceededNotification),
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.reject,
            effects=[
                NotificationEffect(ActivityRejectedNotification),
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                RelatadTransitionEffect('participants', ParticipantStateMachine.cancel)
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.cancel,
            effects=[
                NotificationEffect(ActivityCancelledNotification),
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                RelatadTransitionEffect('participants', ParticipantStateMachine.cancel)
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.restore,
            effects=[
                RelatadTransitionEffect('participants', ParticipantStateMachine.restore),
                NotificationEffect(ActivityRestoredNotification)
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.expire,
            effects=[
                NotificationEffect(ActivityExpiredNotification),
                RelatadTransitionEffect('participants', ParticipantStateMachine.cancel)
            ]
        ),
    ]


