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
    subject = ('Please share the impact results for your activity "{title}".')
    template = 'messages/activity_impact_reminder'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        return [self.obj.owner]
