# -*- coding: utf-8 -*-
from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class EventSucceededOwnerMessage(TransitionMessage):
    subject = _(u'Your event "{title}" took place! 🎉')
    template = 'messages/event_succeeded_owner'
    context = {
        'title': 'title'
    }


class EventRejectedOwnerMessage(TransitionMessage):
    subject = _('Your event "{title}" has been rejected')
    template = 'messages/event_rejected_owner'
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
    subject = _('The date and time for your event "{title}" changed')
    template = 'messages/event_date_changed'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """participants that signed up"""
        from bluebottle.events.models import Participant
        return [
            intention.user for intention
            in self.obj.intentions.instance_of(
                Participant
            ).filter(status='new')
        ]


class EventReminderMessage(TransitionMessage):
    subject = _('Your event "{title}" will take place in 5 days!')
    template = 'messages/event_reminder'
    context = {
        'title': 'title'
    }
    send_once = True

    def get_recipients(self):
        """participants that signed up"""
        from bluebottle.events.models import Participant

        return [
            intention.user for intention
            in self.obj.intentions.instance_of(
                Participant
            ).filter(status='new')
        ]


class ParticipantApplicationMessage(TransitionMessage):
    subject = _('You were added to the event "{title}"')
    template = 'messages/participant_application'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """the participant"""
        return [self.obj.user]


class ParticipantApplicationManagerMessage(TransitionMessage):
    subject = _('A new member just signed up for your event "{title}"')
    template = 'messages/participant_application_manager'
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
    subject = _('You have been rejected for the event "{title}"')
    template = 'messages/participant_rejected'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """the participant"""
        return [self.obj.user]
