# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from bluebottle.events.models import Event, Participant
from bluebottle.notifications.messages import TransitionMessage


class EventSucceededOwnerMessage(TransitionMessage):
    """
    Event was completed successfully
    """
    subject = _(u'Your event "{title}" took place! 🎉')
    template = 'messages/event_succeeded_owner'
    model = Event
    context = {
        'title': 'title'
    }


class EventRejectedOwnerMessage(TransitionMessage):
    """
    Participant was rejected
    """
    subject = _('Your event "{title}" has been rejected')
    template = 'messages/event_rejected_owner'
    model = Event
    context = {
        'title': 'title'
    }


class EventCancelledMessage(TransitionMessage):
    subject = _('Your event "{title}" has been cancelled')
    template = 'messages/event_cancelled'
    context = {
        'title': 'title'
    }


class EventExpiredMessage(TransitionMessage):
    subject = _('Your event "{title}" has been cancelled')
    template = 'messages/event_expired'
    context = {
        'title': 'title'
    }


class EventDateChanged(TransitionMessage):
    """
    Event date did change
    """
    subject = _('The date and time for your event "{title}" changed')
    template = 'messages/event_date_changed'
    model = Event
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """participants that signed up"""
        from bluebottle.events.models import Participant
        return [
            contribution.user for contribution
            in self.obj.contributions.instance_of(
                Participant
            ).filter(status='new')
        ]


class EventReminderMessage(TransitionMessage):
    """
    Event will take place in 5 days
    """
    subject = _('Your event "{title}" will take place in 5 days!')
    template = 'messages/event_reminder'
    model = Event
    context = {
        'title': 'title'
    }
    send_once = True

    def get_recipients(self):
        """participants that signed up"""
        from bluebottle.events.models import Participant

        return [
            contribution.user for contribution
            in self.obj.contributions.instance_of(
                Participant
            ).filter(status='new')
        ]


class ParticipantApplicationMessage(TransitionMessage):
    """
    You signed up for the event
    """
    subject = _('You were added to the event "{title}"')
    template = 'messages/participant_application'
    model = Participant
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """the participant"""
        return [self.obj.user]


class ParticipantApplicationManagerMessage(TransitionMessage):
    """
    Someone signed up for your event
    """
    subject = _('A new member just signed up for your event "{title}"')
    template = 'messages/participant_application_manager'
    model = Participant
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """the organizer and the activity manager"""
        return [
            self.obj.activity.owner,
            self.obj.activity.initiative.activity_manager
        ]


class ParticipantRejectedMessage(TransitionMessage):
    """
    You were rejected to take part at the event
    """
    subject = _('You have been rejected for the event "{title}"')
    template = 'messages/participant_rejected'
    model = Participant
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """the participant"""
        return [self.obj.user]
