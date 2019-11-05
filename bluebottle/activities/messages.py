from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class ActivityWallpostOwnerMessage(TransitionMessage):
    subject = _('{author} commented on your activity')
    template = 'messages/activity_wallpost_owner'

    context = {
        'author': 'author.first_name'
    }

    def get_recipients(self):
        if self.obj.author != self.obj.content_object.owner:
            return [self.obj.content_object.owner]
        else:
            return []


class ActivityWallpostReactionMessage(TransitionMessage):
    subject = _('{author} replied on your comment')
    template = 'messages/activity_wallpost_reaction'

    context = {
        'author': 'author.first_name'
    }

    def get_recipients(self):
        return [self.obj.wallpost.author]


class ActivityWallpostOwnerReactionMessage(TransitionMessage):
    subject = _('{author} commented on your activity')
    template = 'messages/activity_wallpost_owner_reaction'

    context = {
        'author': 'author.first_name'
    }

    def get_recipients(self):
        if self.obj.author != self.obj.wallpost.content_object.owner:
            return [self.obj.wallpost.content_object.owner]
        else:
            return []


class ActivityWallpostFollowerMessage(TransitionMessage):
    subject = _("New post on '{title}'")
    template = 'messages/activity_wallpost_follower'
    context = {
        'title': 'content_object.title'
    }

    def get_recipients(self):
        activity = self.obj.content_object
        follows = activity.follows.filter(
            user__campaign_notifications=True
        ).exclude(
            user__in=(self.obj.author, self.obj.content_object.owner)
        )

        return [follow.user for follow in follows]
