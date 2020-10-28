from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class InitiativeApprovedOwnerMessage(TransitionMessage):
    subject = _('Your initiative "{title}" has been approved!')
    template = 'messages/initiative_approved_owner'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the initiator"""
        return [self.obj.owner]


class InitiativeNeedsWorkOwnerMessage(TransitionMessage):
    subject = _('Your initiative "{title}" needs work')
    template = 'messages/initiative_needs_work_owner'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the initiator"""
        return [self.obj.owner]


class InitiativeRejectedOwnerMessage(TransitionMessage):
    subject = _('Your initiative "{title}" has been rejected.')
    template = 'messages/initiative_rejected_owner'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the initiator"""
        return [self.obj.owner]


class InitiativeCancelledOwnerMessage(TransitionMessage):
    subject = _('The initiative "{title}" has been cancelled.')
    template = 'messages/initiative_cancelled_owner'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the initiator"""
        return [self.obj.owner]


class AssignedReviewerMessage(TransitionMessage):
    subject = _('You are assigned to review "{title}".')
    template = 'messages/assigned_reviewer'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the reviewer"""
        return [self.obj.reviewer]


class InitiativeWallpostOwnerMessage(TransitionMessage):
    subject = _("You have a new post on '{title}'")
    template = 'messages/initiative_wallpost_owner'

    context = {
        'title': 'content_object.title'
    }

    def get_recipients(self):
        """"the initiator"""
        if self.obj.author != self.obj.content_object.owner:
            return [self.obj.content_object.owner]
        else:
            return []


class InitiativeWallpostReactionMessage(TransitionMessage):
    subject = _("You have a new post on '{title}'")
    template = 'messages/initiative_wallpost_reaction'

    context = {
        'title': 'wallpost.content_object.title'
    }

    def get_recipients(self):
        """the wallpost author"""
        return [self.obj.wallpost.author]


class InitiativeWallpostOwnerReactionMessage(TransitionMessage):
    subject = _("You have a new post on '{title}'")
    template = 'messages/initiative_wallpost_owner_reaction'

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
    subject = _("Update from '{title}'")
    template = 'messages/initiative_wallpost_follower'
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

        return {follow.user for follow in follows}
