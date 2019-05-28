from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class InitiativeApproveOwnerMessage(TransitionMessage):
    subject = _('Your initiative has been approved')
    template = 'messages/initiative_approved_owner'


class InitiativeNeedsWorkOwnerMessage(TransitionMessage):
    subject = _('Your initiative needs work')
    template = 'messages/initiative_needs_work_owner'


class InitiativeClosedOwnerMessage(TransitionMessage):
    subject = _('Your initiative has been closed')
    template = 'messages/initiative_closed_owner'
