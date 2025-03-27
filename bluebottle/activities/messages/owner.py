from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class OwnerActivityNotification(TransitionMessage):
    context = {
        'title': 'title',
    }

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    action_title = pgettext('email', 'Open your activity')

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ImpactReminderMessage(OwnerActivityNotification):
    subject = pgettext('email', 'Please share the impact results for your activity "{title}".')
    template = 'messages/activity_impact_reminder'
    context = {
        'title': 'title'
    }


class ActivitySucceededNotification(OwnerActivityNotification):
    """
    The activity succeeded
    """
    subject = pgettext('email', 'Your activity "{title}" has succeeded 🎉')
    template = 'messages/activity_succeeded'


class ActivityRestoredNotification(OwnerActivityNotification):
    """
    The activity was restored
    """
    subject = pgettext('email', 'The activity "{title}" has been restored')
    template = 'messages/activity_restored'


class ActivityRejectedNotification(OwnerActivityNotification):
    """
    The activity was rejected
    """
    subject = pgettext('email', 'Your activity "{title}" has been rejected')
    template = 'messages/activity_rejected'


class ActivityCancelledNotification(OwnerActivityNotification):
    """
    The activity got cancelled
    """
    subject = pgettext('email', 'Your activity "{title}" has been cancelled')
    template = 'messages/activity_cancelled'


class ActivityExpiredNotification(OwnerActivityNotification):
    """
    The activity expired (no sign-ups before registration deadline or start date)
    """
    subject = pgettext('email', 'The registration deadline for your activity "{title}" has expired')
    template = 'messages/activity_expired'


class ParticipantWithdrewConfirmationNotification(OwnerActivityNotification):
    """
    The participant withdrew from the activity
    """
    context = {
        'title': 'activity.title',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    subject = pgettext('email', 'You have withdrawn from the activity "{title}"')
    template = 'messages/participant_withdrew_confirmation'


class PublishActivityReminderNotification(OwnerActivityNotification):
    subject = pgettext('email', 'Publish your activity "{title}"')
    template = 'messages/publish_activity_reminder'
    send_once = True

    context = {
        'title': 'title',
    }

    action_title = pgettext('email', 'Publish your activity')
