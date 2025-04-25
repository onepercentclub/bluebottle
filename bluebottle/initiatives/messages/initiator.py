from django.utils.translation import gettext_lazy as _, pgettext

from bluebottle.notifications.messages import TransitionMessage


class InitiativeInitiatorMessage(TransitionMessage):
    context = {
        'title': 'title'
    }

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    action_title = pgettext('email', 'View initiative')

    def get_recipients(self):
        """the initiator"""
        return [self.obj.owner]


class InitiativeSubmittedInitiatorMessage(InitiativeInitiatorMessage):
    subject = _('You submitted an initiative on {site_name}')
    template = 'messages/initiator/initiative_submitted'


class InitiativeApprovedInitiatorMessage(InitiativeInitiatorMessage):
    subject = _('Your initiative on {site_name} has been approved!')
    template = 'messages/initiator/initiative_approved'


class InitiativePublishedInitiatorMessage(InitiativeInitiatorMessage):
    subject = _('Your initiative on {site_name} has been published!')
    template = 'messages/initiator/initiative_published'


class InitiativeNeedsWorkInitiatorMessage(InitiativeInitiatorMessage):
    subject = _('The initiative you submitted on {site_name} needs work')
    template = 'messages/initiator/initiative_needs_work'


class InitiativeRejectedInitiatorMessage(InitiativeInitiatorMessage):
    subject = _('Your initiative on {site_name} has been rejected')
    template = 'messages/initiator/initiative_rejected'


class InitiativeCancelledInitiatorMessage(InitiativeInitiatorMessage):
    subject = _('The initiative "{title}" has been cancelled.')
    template = 'messages/initiator/initiative_cancelled'
