from functools import lru_cache


@lru_cache()
def get_activity_messages():
    from bluebottle.activities.messages.participant import InactiveParticipantAddedNotification
    from bluebottle.collect.messages import (
        CollectThankYouNotification,
        ParticipantJoinedNotification as CollectParticipantJoinedNotification,
    )
    from bluebottle.collect.models import CollectActivity
    from bluebottle.deeds.messages import (
        DeedThankYouNotification,
        ParticipantJoinedNotification as DeedParticipantJoinedNotification,
    )
    from bluebottle.deeds.models import Deed
    from bluebottle.time_based.messages import (
        ParticipantAddedNotification,
        ParticipantSlotParticipantRegisteredNotification,
        TeamAddedNotification,
    )
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
    from bluebottle.time_based.messages.thank_you import (
        DateParticipantThankYouNotification,
        PeriodicActivityThankYouNotification,
        RegistrationActivityThankYouNotification,
        ScheduleParticipantThankYouNotification,
        TeamThankYouNotification,
    )
    from bluebottle.time_based.models import (
        DateActivity, DeadlineActivity, PeriodicActivity, ScheduleActivity
    )

    added = (ParticipantAddedNotification, InactiveParticipantAddedNotification)

    return {
        DateActivity: {
            'join': (ParticipantSlotParticipantRegisteredNotification, ) + added,
            'apply': (DateUserAppliedNotification, ),
            'accept': (UserRegistrationAcceptedNotification, ),
            'reject': (UserRegistrationRejectedNotification, ),
            'succeed': (DateParticipantThankYouNotification, ),
        },
        DeadlineActivity: {
            'join': (DeadlineUserJoinedNotification, ) + added,
            'apply': (DeadlineUserAppliedNotification, ),
            'accept': (UserRegistrationAcceptedNotification, ),
            'reject': (UserRegistrationRejectedNotification, ),
            'succeed': (RegistrationActivityThankYouNotification, ),
        },
        PeriodicActivity: {
            'join': (PeriodicUserJoinedNotification, ) + added,
            'apply': (PeriodicUserAppliedNotification, ),
            'accept': (UserRegistrationAcceptedNotification, ),
            'reject': (UserRegistrationRejectedNotification, ),
            'succeed': (PeriodicActivityThankYouNotification, ),
        },
        ScheduleActivity: {
            'join': (ScheduleUserJoinedNotification, TeamJoinedNotification, TeamAddedNotification) + added,
            'apply': (ScheduleUserAppliedNotification, TeamAppliedNotification),
            'accept': (UserRegistrationAcceptedNotification, UserTeamRegistrationAcceptedNotification),
            'reject': (UserRegistrationRejectedNotification, UserTeamRegistrationRejectedNotification),
            'succeed': (ScheduleParticipantThankYouNotification, TeamThankYouNotification),
        },
        Deed: {
            'join': (DeedParticipantJoinedNotification, ) + added,
            'succeed': (DeedThankYouNotification, ),
        },
        CollectActivity: {
            'join': (CollectParticipantJoinedNotification, ) + added,
            'succeed': (CollectThankYouNotification, ),
        },
    }


def get_activity_actions(activity):
    return get_activity_messages().get(activity.get_real_instance_class(), {})


def get_customisable_actions(activity):
    if getattr(activity, 'review', False):
        actions = ('accept', 'reject', 'succeed')
    else:
        actions = ('join', 'succeed')
    return [action for action in actions if action in get_activity_actions(activity)]


def get_message_action(activity, message):
    for action, message_classes in get_activity_actions(activity).items():
        if type(message) in message_classes:
            return action
