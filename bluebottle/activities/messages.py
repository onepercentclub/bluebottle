from bluebottle.initiatives.models import InitiativePlatformSettings

from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class ActivityWallpostOwnerMessage(TransitionMessage):
    subject = _("You have a new post on '{title}'")
    template = 'messages/activity_wallpost_owner'

    context = {
        'title': 'content_object.title'
    }

    def get_recipients(self):
        """activity organizer"""
        if self.obj.author != self.obj.content_object.owner:
            return [self.obj.content_object.owner]
        else:
            return []


class ActivityWallpostReactionMessage(TransitionMessage):
    subject = _("You have a new post on '{title}'")
    template = 'messages/activity_wallpost_reaction'

    context = {
        'title': 'wallpost.content_object.title'
    }

    @property
    def action_link(self):
        return self.obj.get_absolute_url()


class ActivityWallpostOwnerReactionMessage(TransitionMessage):
    subject = _("You have a new post on '{title}'")
    template = 'messages/activity_wallpost_owner_reaction'

    context = {
        'title': 'wallpost.content_object.title'
    }

    def get_recipients(self):
        """activity organizer"""
        if self.obj.author != self.obj.wallpost.content_object.owner:
            return [self.obj.wallpost.content_object.owner]
        else:
            return []


class ActivityWallpostFollowerMessage(TransitionMessage):
    subject = _("Update from '{title}'")
    template = 'messages/activity_wallpost_follower'
    context = {
        'title': 'content_object.title'
    }

    def get_recipients(self):
        """followers of the activity"""
        activity = self.obj.content_object
        follows = activity.follows.filter(
            user__campaign_notifications=True
        ).exclude(
            user__in=(self.obj.author, self.obj.content_object.owner)
        )

        return [follow.user for follow in follows]


class ImpactReminderMessage(TransitionMessage):
    subject = (u'Please share the impact results for your activity "{title}".')
    template = 'messages/activity_impact_reminder'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        return [self.obj.owner]


class ActivityNotification(TransitionMessage):
    context = {
        'title': 'title',
    }

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    action_title = _('Open your activity')

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context['impact'] = InitiativePlatformSettings.load().enable_impact

        return context

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ActivitySucceededNotification(ActivityNotification):
    """
    The activity succeeded
    """
    subject = _('Your activity "{title}" has succeeded 🎉')
    template = 'messages/activity_succeeded'


class ActivityRestoredNotification(ActivityNotification):
    """
    The activity was restored
    """
    subject = _('The activity "{title}" has been restored')
    template = 'messages/activity_restored'


class ActivityRejectedNotification(ActivityNotification):
    """
    The activity was rejected
    """
    subject = _('Your activity "{title}" has been rejected')
    template = 'messages/activity_rejected'


class ActivityCancelledNotification(ActivityNotification):
    """
    The activity got cancelled
    """
    subject = _('Your activity "{title}" has been cancelled')
    template = 'messages/activity_cancelled'


class ActivityExpiredNotification(ActivityNotification):
    """
    The activity expired (no sign-ups before registration deadline or start date)
    """
    subject = _('The registration deadline for your activity "{title}" has expired')
    template = 'messages/activity_expired'
