from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class EventDoneOwnerMessage(TransitionMessage):
    subject = _('Your event is completed')
    template = 'messages/event_done_owner'


class EventClosedOwnerMessage(TransitionMessage):
    subject = _('Your event has been closed')
    template = 'messages/event_closed_owner'
