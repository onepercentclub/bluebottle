from bluebottle.activities.models import Activity

from bluebottle.wallposts.models import Wallpost, Reaction

from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class ActivityWallpostOwnerMessage(TransitionMessage):
    """
    Your activity wall received a post.
    """
    subject = _("You have a new post on '{title}'")
    template = 'messages/activity_wallpost_owner'
    model = Wallpost

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
    """
    Your post on an activity wall received a reaction.
    """
    subject = _("You have a new post on '{title}'")
    template = 'messages/activity_wallpost_reaction'
    model = Reaction

    context = {
        'title': 'wallpost.content_object.title'
    }

    def get_recipients(self):
        """wallpost author"""
        return [self.obj.wallpost.author]


class ActivityWallpostOwnerReactionMessage(TransitionMessage):
    """
    Your activity wall received a reaction to a post.
    """
    subject = _("You have a new post on '{title}'")
    template = 'messages/activity_wallpost_owner_reaction'
    model = Reaction

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
    """
    An activity you are following received a post.
    """
    subject = _("Update from '{title}'")
    template = 'messages/activity_wallpost_follower'
    model = Wallpost

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
    """
    Your activity is completed, but you haven't filled in your impact results.
    """
    subject = (u'Please share the impact results for your activity "{title}".')
    template = 'messages/activity_impact_reminder'
    model = Activity

    context = {
        'title': 'title'
    }
