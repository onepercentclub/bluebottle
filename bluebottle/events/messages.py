from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class EventSucceededOwnerMessage(TransitionMessage):
    subject = _('The status of your event was changed to successful')
    template = 'messages/event_succeeded_owner'


class EventClosedOwnerMessage(TransitionMessage):
    subject = _('Your event has been closed')
    template = 'messages/event_closed_owner'


class EventDateChanged(TransitionMessage):
    subject = _('The date and time for your event changed')
    template = 'messages/event_date_changed'

    def get_recipients(self):
        return [
            contribution.user for contribution
            in self.obj.contributions.filter(status='new')
        ]
