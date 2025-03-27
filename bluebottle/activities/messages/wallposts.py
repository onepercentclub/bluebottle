from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class ActivityWallpostOwnerMessage(TransitionMessage):
    subject = pgettext('email', "You have a new post on '{title}'")
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
    subject = pgettext('email', "You have a new post on '{title}'")
    template = 'messages/activity_wallpost_reaction'

    context = {
        'title': 'wallpost.content_object.title'
    }
    action_title = pgettext('email', 'View response')

    def get_recipients(self):
        """wallpost author"""
        return [self.obj.wallpost.author]


class ActivityWallpostOwnerReactionMessage(TransitionMessage):
    subject = pgettext('email', "You have a new post on '{title}'")
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
    subject = pgettext('email', "Update from '{title}'")
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
