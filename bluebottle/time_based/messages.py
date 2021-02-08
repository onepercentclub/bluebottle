# -*- coding: utf-8 -*-
from django.template import defaultfilters
from django.utils.translation import ugettext_lazy as _

from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.notifications.messages import TransitionMessage


class SlotDateChangedNotification(TransitionMessage):
    """
    The date of the slot changed
    """
    subject = _('The date and time for a slot of your activity "{title}" has changed')
    template = 'messages/slot_date_changed'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.accepted_participants
        ]


class DeadlineChangedNotification(TransitionMessage):
    """
    The deadline of the activity changed
    """
    subject = _('The deadline for your activity "{title}" changed')
    template = 'messages/deadline_changed'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.accepted_participants
        ]


class ReminderSingleDateNotification(TransitionMessage):
    """
    Reminder notification for a single date activity
    """
    subject = _('The activity "{title}" will take place in a few days!')
    template = 'messages/reminder_single_date'
    send_once = True
    context = {
        'title': 'title',
    }

    def get_context(self, recipient):
        context = super().get_context(recipient)
        slot = self.obj.slots.filter(slot_participants__participant__user=recipient).first()
        context['start_date'] = defaultfilters.date(slot.start)
        context['start_time'] = defaultfilters.time(slot.start)
        context['end_time'] = defaultfilters.time(slot.end)
        return context

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.accepted_participants
        ]


class ReminderMultipleDatesNotification(TransitionMessage):
    """
    Reminder notification for an activity over multiple dates
    """
    subject = _('The activity "{title}" will take place in a few days!')
    template = 'messages/reminder_multiple_dates'
    # send_once = True
    context = {
        'title': 'title',
    }

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context['slots'] = []
        slots = self.obj.slots.filter(
            slot_participants__participant__user=recipient,
            slot_participants__status='registered'
        )
        for slot in slots:
            context['slots'].append({
                'title': slot.title,
                'start_date': defaultfilters.date(slot.start),
                'start_time': defaultfilters.time(slot.start),
                'end_time': defaultfilters.time(slot.end)
            })
        return context

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.accepted_participants
        ]


class ActivitySucceededNotification(TransitionMessage):
    """
    The activity succeeded
    """
    subject = _('Your activity "{title}" has succeeded 🎉')
    template = 'messages/activity_succeeded'
    context = {
        'title': 'title'
    }

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context['impact'] = InitiativePlatformSettings.load().enable_impact

        return context

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ActivitySucceededManuallyNotification(TransitionMessage):
    """
    The activity was set to succeeded manually
    """
    subject = _('The activity "{title}" has succeeded 🎉')
    template = 'messages/activity_succeeded_manually'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.accepted_participants
        ]


class ActivityRejectedNotification(TransitionMessage):
    """
    The activity was rejected
    """
    subject = _('Your activity "{title}" has been rejected')
    template = 'messages/activity_rejected'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ActivityCancelledNotification(TransitionMessage):
    """
    The activity got cancelled
    """
    subject = _('Your activity "{title}" has been cancelled')
    template = 'messages/activity_cancelled'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ActivityExpiredNotification(TransitionMessage):
    """
    The activity expired (no sign-ups before registration deadline or start date)
    """
    subject = _('The registration deadline for your activity "{title}" has expired')
    template = 'messages/activity_expired'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ParticipantAddedNotification(TransitionMessage):
    """
    A participant was added manually (through back-office)
    """
    subject = _('You have been added to the activity "{title}" 🎉')
    template = 'messages/participant_added'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class ParticipantCreatedNotification(TransitionMessage):
    """
    A participant applied  for the activity and should be reviewed
    """
    subject = _('You have a new participant for your activity "{title}" 🎉')
    template = 'messages/participant_created'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.activity.owner]


class NewParticipantNotification(TransitionMessage):
    """
    A participant joined the activity (no review required)
    """
    subject = _('A new participant has joined your activity "{title}" 🎉')
    template = 'messages/new_participant'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.activity.owner]


class ParticipantAcceptedNotification(TransitionMessage):
    """
    The participant got accepted after review
    """
    subject = _('You have been selected for the activity "{title}" 🎉')
    template = 'messages/participant_accepted'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class ParticipantRejectedNotification(TransitionMessage):
    """
    The participant got rejected after revie
    """
    subject = _('You have not been selected for the activity "{title}"')
    template = 'messages/participant_rejected'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class ParticipantRemovedNotification(TransitionMessage):
    """
    The participant was removed from the activity
    """
    subject = _('You have been removed as participant for the activity "{title}"')
    template = 'messages/participant_removed'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """participant"""
        return [self.obj.user]
