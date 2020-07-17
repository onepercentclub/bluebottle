from bluebottle.initiatives.models import Initiative

from bluebottle.wallposts.models import Wallpost, Reaction

from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class InitiativeApprovedOwnerMessage(TransitionMessage):
    """
    Your initiative has been approved
    """
    subject = _('Your initiative "{title}" has been approved!')
    template = 'messages/initiative_approved_owner'
    model = Initiative
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the initiator"""
        return [self.obj.owner]


class InitiativeRejectedOwnerMessage(TransitionMessage):
    """
    Your initiative has been rejected
    """
    subject = _('Your initiative "{title}" has been rejected.')
    template = 'messages/initiative_rejected_owner'
    model = Initiative
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the initiator"""
        return [self.obj.owner]


class InitiativeCancelledOwnerMessage(TransitionMessage):
    """
    Your initiative has been cancelled
    """
    subject = _('The initiative "{title}" has been cancelled.')
    template = 'messages/initiative_cancelled_owner'
    model = Initiative
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the initiator"""
        return [self.obj.owner]


class AssignedReviewerMessage(TransitionMessage):
    """
    You were assigned as reviewer for an initiative
    """
    subject = _('You are assigned to review "{title}".')
    template = 'messages/assigned_reviewer'
    model = Initiative
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the reviewer"""
        return [self.obj.reviewer]


class InitiativeWallpostOwnerMessage(TransitionMessage):
    """
    Your initiative received a wallpost
    """
    subject = _("You have a new post on '{title}'")
    template = 'messages/initiative_wallpost_owner'
    model = Wallpost
    context = {
        'title': 'content_object.title'
    }

    def get_recipients(self):
        """the initiator"""
        if self.obj.author != self.obj.content_object.owner:
            return [self.obj.content_object.owner]
        else:
            return []


class InitiativeWallpostReactionMessage(TransitionMessage):
    """
    Someone commented on your wallpost
    """
    subject = _("You have a new post on '{title}'")
    template = 'messages/initiative_wallpost_reaction'
    model = Reaction
    context = {
        'title': 'wallpost.content_object.title'
    }

    def get_recipients(self):
        """the wallpost author"""
        return [self.obj.wallpost.author]


class InitiativeWallpostOwnerReactionMessage(TransitionMessage):
    """
    Someone commented on a wallpost on your initiative
    """
    subject = _("You have a new post on '{title}'")
    template = 'messages/initiative_wallpost_owner_reaction'
    model = Reaction
    context = {
        'title': 'wallpost.content_object.title'
    }

    def get_recipients(self):
        """the initiator"""
        if self.obj.author != self.obj.wallpost.content_object.owner:
            return [self.obj.wallpost.content_object.owner]
        else:
            return []


class InitiativeWallpostFollowerMessage(TransitionMessage):
    """
    There is a new wallpost on the initiative your following
    """
    subject = _("Update from '{title}'")
    template = 'messages/initiative_wallpost_follower'
    model = Wallpost
    context = {
        'title': 'content_object.title'
    }

    def get_recipients(self):
        """followers of the initiative"""
        initiative = self.obj.content_object
        follows = []
        for activity in initiative.activities.filter(
            status__in=(
                'succeeded',
                'open',
                'partially_funded',
                'full',
                'running'
            )

        ):
            follows += activity.follows.filter(
                user__campaign_notifications=True
            ).exclude(
                user__in=(self.obj.author, initiative.owner)
            )

        return set(follow.user for follow in follows)
