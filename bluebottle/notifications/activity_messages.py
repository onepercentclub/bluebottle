from functools import lru_cache


@lru_cache()
def get_activity_messages():
    from bluebottle.collect.messages import (
        ParticipantJoinedNotification as CollectParticipantJoinedNotification
    )
    from bluebottle.collect.models import CollectActivity
    from bluebottle.deeds.messages import (
        ParticipantJoinedNotification as DeedParticipantJoinedNotification
    )
    from bluebottle.deeds.models import Deed
    from bluebottle.time_based.messages import ParticipantSlotParticipantRegisteredNotification
    from bluebottle.time_based.messages.registrations import (
        DateUserAppliedNotification,
        DeadlineUserAppliedNotification,
        DeadlineUserJoinedNotification,
        PeriodicUserAppliedNotification,
        PeriodicUserJoinedNotification,
        ScheduleUserAppliedNotification,
        ScheduleUserJoinedNotification,
        TeamAppliedNotification,
        TeamJoinedNotification,
        UserRegistrationAcceptedNotification,
        UserRegistrationRejectedNotification,
        UserTeamRegistrationAcceptedNotification,
        UserTeamRegistrationRejectedNotification,
    )
    from bluebottle.time_based.models import (
        DateActivity, DeadlineActivity, PeriodicActivity, ScheduleActivity
    )

    return {
        DateActivity: {
            'join': (ParticipantSlotParticipantRegisteredNotification, ),
            'apply': (DateUserAppliedNotification, ),
            'accept': (UserRegistrationAcceptedNotification, ),
            'reject': (UserRegistrationRejectedNotification, ),
        },
        DeadlineActivity: {
            'join': (DeadlineUserJoinedNotification, ),
            'apply': (DeadlineUserAppliedNotification, ),
            'accept': (UserRegistrationAcceptedNotification, ),
            'reject': (UserRegistrationRejectedNotification, ),
        },
        PeriodicActivity: {
            'join': (PeriodicUserJoinedNotification, ),
            'apply': (PeriodicUserAppliedNotification, ),
            'accept': (UserRegistrationAcceptedNotification, ),
            'reject': (UserRegistrationRejectedNotification, ),
        },
        ScheduleActivity: {
            'join': (ScheduleUserJoinedNotification, TeamJoinedNotification),
            'apply': (ScheduleUserAppliedNotification, TeamAppliedNotification),
            'accept': (UserRegistrationAcceptedNotification, UserTeamRegistrationAcceptedNotification),
            'reject': (UserRegistrationRejectedNotification, UserTeamRegistrationRejectedNotification),
        },
        Deed: {
            'join': (DeedParticipantJoinedNotification, ),
        },
        CollectActivity: {
            'join': (CollectParticipantJoinedNotification, ),
        },
    }


def get_activity_actions(activity):
    return get_activity_messages().get(activity.get_real_instance_class(), {})


def get_message_action(activity, message):
    for action, message_classes in get_activity_actions(activity).items():
        if type(message) in message_classes:
            return action
