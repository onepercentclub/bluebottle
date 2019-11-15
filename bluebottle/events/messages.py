from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class EventSucceededOwnerMessage(TransitionMessage):
    subject = _('You completed your event "{title}"!')
    template = 'messages/event_succeeded_owner'
    context = {
        'title': 'title'
    }


class EventClosedOwnerMessage(TransitionMessage):
    subject = _('Your event "{title}" has been closed')
    template = 'messages/event_closed_owner'
    context = {
        'title': 'title'
    }


class EventDateChanged(TransitionMessage):
    subject = _('The date and time for your event "{title}" changed')
    template = 'messages/event_date_changed'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        return [
            contribution.user for contribution
            in self.obj.contributions.filter(status='new')
        ]


class EventReminder(TransitionMessage):
    subject = _('Your event "{title}" will take place in 5 days!')
    template = 'messages/event_reminder'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        return [
            contribution.user for contribution
            in self.obj.contributions.filter(status='new')
        ]


class ParticipantApplicationMessage(TransitionMessage):
    subject = _('You were added to the event "{title}"')
    template = 'messages/participant_application'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        return [self.obj.user]


class ParticipantRejectedMessage(TransitionMessage):
    subject = _('Your status for "{title}" was changed to "not going"')
    template = 'messages/participant_rejected'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        return [self.obj.user]
