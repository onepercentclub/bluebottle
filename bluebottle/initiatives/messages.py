from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class InitiativeApproveOwnerMessage(TransitionMessage):
    subject = _('Your initiative "{initiative_title}" has been approved!')
    template = 'messages/initiative_approved_owner'
    context = {
        'initiative_title': 'title'
    }


class InitiativeNeedsWorkOwnerMessage(TransitionMessage):
    subject = _('Your initiative "{initiative_title}" needs work')
    template = 'messages/initiative_needs_work_owner'
    context = {
        'initiative_title': 'title'
    }


class InitiativeClosedOwnerMessage(TransitionMessage):
    subject = _('Your initiative "{initiative_title}" has been closed')
    template = 'messages/initiative_closed_owner'
    context = {
        'initiative_title': 'title'
    }


class InitiativeWallpostOwnerMessage(TransitionMessage):
    subject = _('{author} commented on your initiative')
    template = 'messages/initiative_wallpost_owner'

    context = {
        'author': 'author.first_name'
    }

    def get_recipients(self):
        if self.obj.author != self.obj.content_object.owner:
            return [self.obj.content_object.owner]
        else:
            return []


class InitiativeWallpostReactionMessage(TransitionMessage):
    subject = _('{author} replied on your comment')
    template = 'messages/initiative_wallpost_reaction'

    context = {
        'author': 'author.first_name'
    }

    def get_recipients(self):
        return [self.obj.wallpost.author]


class InitiativeWallpostOwnerReactionMessage(TransitionMessage):
    subject = _('{author} commented on your initiative')
    template = 'messages/initiative_wallpost_owner_reaction'

    context = {
        'author': 'author.first_name'
    }

    def get_recipients(self):
        if self.obj.author != self.obj.wallpost.content_object.owner:
            return [self.obj.wallpost.content_object.owner]
        else:
            return []


class InitiativeWallpostFollowerMessage(TransitionMessage):
    subject = _("New post on '{title}'")
    template = 'messages/initiative_wallpost_follower'
    context = {
        'title': 'content_object.title'
    }

    def get_recipients(self):
        initiative = self.obj.content_object
        follows = initiative.follows.filter(
            user__campaign_notifications=True
        ).exclude(
            user__in=(self.obj.author, self.obj.content_object.owner)
        )

        return [follow.user for follow in follows]
