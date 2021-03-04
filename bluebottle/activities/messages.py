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

    def get_recipients(self):
        """wallpost author"""
        return [self.obj.wallpost.author]


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


class ActivitySucceededNotification(TransitionMessage):
    """
    The activity succeeded
    """
    subject = _('Your activity "{title}" has succeeded 🎉')
    template = 'messages/activity_succeeded'
    context = {
        'title': 'title',
        'activity_url': 'get_absolute_url'
    }

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context['impact'] = InitiativePlatformSettings.load().enable_impact

        return context

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ActivityRestoredNotification(TransitionMessage):
    """
    The activity was restored
    """
    subject = _('The activity "{title}" has been restored')
    template = 'messages/activity_restored'
    context = {
        'title': 'title',
        'activity_url': 'get_absolute_url'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ActivityRejectedNotification(TransitionMessage):
    """
    The activity was rejected
    """
    subject = _('Your activity "{title}" has been rejected')
    template = 'messages/activity_rejected'
    context = {
        'title': 'title',
        'activity_url': 'get_absolute_url'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ActivityCancelledNotification(TransitionMessage):
    """
    The activity got cancelled
    """
    subject = _('Your activity "{title}" has been cancelled')
    template = 'messages/activity_cancelled'
    context = {
        'title': 'title',
        'activity_url': 'get_absolute_url'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ActivityExpiredNotification(TransitionMessage):
    """
    The activity expired (no sign-ups before registration deadline or start date)
    """
    subject = _('The registration deadline for your activity "{title}" has expired')
    template = 'messages/activity_expired'
    context = {
        'title': 'title',
        'activity_url': 'get_absolute_url'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]
