from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class FollowersNotification(TransitionMessage):
    subject = pgettext('email', "New update from '{title}'")

    template = 'messages/update_followers'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """followers of the activity"""
        activity = self.obj.activity
        follows = activity.follows.filter(
            user__campaign_notifications=True
        ).exclude(
            user__in=(self.obj.author, self.obj.activity.owner)
        )

        return [follow.user for follow in follows]


class OwnerNotification(TransitionMessage):
    subject = pgettext('email', "A new message is posted on '{title}'")

    template = 'messages/update_owner'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """followers of the activity"""
        if self.obj.author != self.obj.activity.owner:
            return [self.obj.activity.owner]
        else:
            return []


class ParentNotification(TransitionMessage):
    subject = pgettext('email', "You have a reply on '{title}'")

    template = 'messages/update_parent'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """followers of the activity"""
        if self.obj.parent:
            return [self.obj.parent.author]
        else:
            return []
