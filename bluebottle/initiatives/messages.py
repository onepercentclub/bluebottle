from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class InitiativeApproveOwnerMessage(TransitionMessage):
    subject = _('Your initiative {initiative_title} has been approved!')
    template = 'messages/initiative_approved_owner'
    context = {
        'initiative_title': 'title'
    }


class InitiativeNeedsWorkOwnerMessage(TransitionMessage):
    subject = _('Your initiative {initiative_title} needs work')
    template = 'messages/initiative_needs_work_owner'
    context = {
        'initiative_title': 'title'
    }


class InitiativeClosedOwnerMessage(TransitionMessage):
    subject = _('Your initiative {initiative_title} has been closed')
    template = 'messages/initiative_closed_owner'
    context = {
        'initiative_title': 'title'
    }
