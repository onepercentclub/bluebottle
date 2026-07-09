from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage
from bluebottle.updates.models import AudienceChoices
from bluebottle.updates.utils import get_active_contributor_users


class UpdateMessage(TransitionMessage):
    class Meta:
        abstract = True

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    context = {
        'title': 'activity.title',
        'author': 'author.short_name',
        'message': 'message.html',
        'update_type': 'update_type',
        'has_media': 'has_media',
    }


class FollowersNotification(UpdateMessage):
    subject = pgettext('platform-email', "New update from '{title}'")
    template = 'messages/update_followers'

    def get_recipients(self):
        """followers of the activity"""
        activity = self.obj.activity
        exclude = (self.obj.author, self.obj.activity.owner)

        if self.obj.audience == AudienceChoices.contributors:
            return get_active_contributor_users(activity, exclude=exclude)

        follows = activity.followers.filter(user__campaign_notifications=True).exclude(user__in=exclude)

        recipients = [follow.user for follow in follows]
        return recipients


class OwnerNotification(UpdateMessage):
    subject = pgettext('platform-email', "A new message is posted on '{title}'")
    template = 'messages/update_owner'

    def get_recipients(self):
        """followers of the activity"""
        if self.obj.author != self.obj.activity.owner:
            return [self.obj.activity.owner]
        else:
            return []


class ParentNotification(UpdateMessage):
    subject = pgettext('platform-email', "You have a reply on '{title}'")
    template = 'messages/update_parent'

    def get_recipients(self):
        """followers of the activity"""
        if self.obj.parent:
            return [self.obj.parent.author]
        else:
            return []
