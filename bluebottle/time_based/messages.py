# -*- coding: utf-8 -*-
from pytz import timezone

from django.template import defaultfilters
from django.utils.translation import pgettext_lazy as pgettext
from django.utils.timezone import get_current_timezone

from bluebottle.clients.utils import tenant_url
from bluebottle.notifications.messages import TransitionMessage


def get_slot_info(slot):
    if slot.location and not slot.is_online:
        tz = timezone(slot.location.timezone)
    else:
        tz = get_current_timezone()

    start = slot.start.astimezone(tz)
    end = slot.end.astimezone(tz)

    return {
        'title': slot.title or str(slot),
        'is_online': slot.is_online,
        'online_meeting_url': slot.online_meeting_url,
        'location': slot.location.formatted_address if slot.location else '',
        'location_hint': slot.location_hint,
        'start_date': defaultfilters.date(start),
        'start_time': defaultfilters.time(start),
        'end_time': defaultfilters.time(end),
        'timezone': start.strftime('%Z')
    }


class DeadlineChangedNotification(TransitionMessage):
    """
    The deadline of the activity changed
    """
    subject = pgettext('email', 'The deadline for your activity "{title}" changed')
    template = 'messages/deadline_changed'
    context = {
        'title': 'title',
    }

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.accepted_participants
        ]


class ReminderSingleDateNotification(TransitionMessage):
    """
    Reminder notification for a single date activity
    """
    subject = pgettext('email', 'The activity "{title}" will take place in a few days!')
    template = 'messages/reminder_single_date'
    send_once = True
    context = {
        'title': 'title',
    }

    def get_context(self, recipient):
        context = super().get_context(recipient)
        slot = self.obj.slots.filter(slot_participants__participant__user=recipient).first()
        context.update(get_slot_info(slot))
        context['title'] = self.obj.title
        return context

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.accepted_participants
        ]


class ReminderMultipleDatesNotification(TransitionMessage):
    """
    Reminder notification for an activity over multiple dates
    """
    subject = pgettext('email', 'The activity "{title}" will take place in a few days!')
    template = 'messages/reminder_multiple_dates'
    send_once = True
    context = {
        'title': 'title',
    }

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context['slots'] = []
        slots = self.obj.slots.filter(
            status__in=['full', 'open', 'running'],
            slot_participants__participant__user=recipient,
            slot_participants__status='registered'
        )
        for slot in slots:
            info = get_slot_info(slot)
            context['slots'].append(info)
        return context

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.accepted_participants
        ]


class ChangedSingleDateNotification(TransitionMessage):
    """
    Notification when slot details (date, time or location) changed for a single date activity
    """
    subject = pgettext('email', 'The details of activity "{title}" have changed')
    template = 'messages/changed_single_date'
    context = {
        'title': 'activity.title',
    }

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context.update(get_slot_info(self.obj))
        context['title'] = self.obj.activity.title
        return context

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.activity.accepted_participants
        ]


class ChangedMultipleDatesNotification(TransitionMessage):
    """
    Notification when slot details (date, time or location) changed for an activity with multiple slots
    """
    subject = pgettext('email', 'The details of activity "{title}" have changed')
    template = 'messages/changed_multiple_dates'
    context = {
        'title': 'activity.title',
    }

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context['slots'] = []
        slots = self.obj.activity.slots.filter(
            status__in=['full', 'open', 'running'],
            slot_participants__participant__user=recipient,
            slot_participants__status='registered'
        ).order_by('start')
        for slot in slots:
            info = get_slot_info(slot)
            info['changed'] = slot.id == self.obj.id
            context['slots'].append(info)
        return context

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.accepted_participants
        ]


class ActivitySucceededManuallyNotification(TransitionMessage):
    """
    The activity was set to succeeded manually
    """
    subject = pgettext('email', 'The activity "{title}" has succeeded 🎉')
    template = 'messages/activity_succeeded_manually'
    context = {
        'title': 'title',
    }

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.accepted_participants
        ]


class ParticipantAddedNotification(TransitionMessage):
    """
    A participant was added manually (through back-office)
    """
    subject = pgettext('email', 'You have been added to the activity "{title}" 🎉')
    template = 'messages/participant_added'
    context = {
        'title': 'activity.title',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'Open your activity')

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class ParticipantCreatedNotification(TransitionMessage):
    """
    A participant applied  for the activity and should be reviewed
    """
    subject = pgettext('email', 'You have a new participant for your activity "{title}" 🎉')
    template = 'messages/participant_created'
    context = {
        'title': 'activity.title',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'Open your activity')

    def get_recipients(self):
        """activity owner"""
        return [self.obj.activity.owner]


class NewParticipantNotification(TransitionMessage):
    """
    A participant joined the activity (no review required)
    """
    subject = pgettext('email', 'A new participant has joined your activity "{title}" 🎉')
    template = 'messages/new_participant'
    context = {
        'title': 'activity.title',
        'applicant_name': 'user.full_name'
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'Open your activity')

    def get_recipients(self):
        """activity owner"""
        return [self.obj.activity.owner]


class ParticipantNotification(TransitionMessage):
    """
    A participant was added manually (through back-office)
    """
    context = {
        'title': 'activity.title',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class ParticipantAcceptedNotification(TransitionMessage):
    """
    The participant got accepted after review
    """
    subject = pgettext('email', 'You have been selected for the activity "{title}" 🎉')
    template = 'messages/participant_accepted'
    context = {
        'title': 'activity.title',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class ParticipantRejectedNotification(TransitionMessage):
    """
    The participant got rejected after revie
    """
    subject = pgettext('email', 'You have not been selected for the activity "{title}"')
    template = 'messages/participant_rejected'
    context = {
        'title': 'activity.title',
    }

    @property
    def action_link(self):
        return tenant_url('/initiatives/activities/list')

    action_title = pgettext('email', 'View all activities')

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class ParticipantRemovedNotification(TransitionMessage):
    """
    The participant was removed from the activity
    """
    subject = pgettext('email', 'You have been removed as participant for the activity "{title}"')
    template = 'messages/participant_removed'
    context = {
        'title': 'activity.title',
    }

    @property
    def action_link(self):
        return tenant_url('/initiatives/activities/list')

    action_title = pgettext('email', 'View all activities')

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class ParticipantFinishedNotification(TransitionMessage):
    """
    The participant was finished
    """
    subject = pgettext('email', 'Your contribution to the activity "{title}" is successful 🎉')
    template = 'messages/participant_finished'
    context = {
        'title': 'activity.title',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class ParticipantWithdrewNotification(TransitionMessage):
    """
    A participant withdrew from your activity
    """
    subject = pgettext('email', 'A participant has withdrawn from your activity "{title}"')
    template = 'messages/participant_withdrew'
    context = {
        'title': 'activity.title',
        'applicant_name': 'user.full_name'
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'Open your activity')

    def get_recipients(self):
        """activity owner"""
        return [self.obj.activity.owner]


class ParticipantAddedOwnerNotification(TransitionMessage):
    """
    A participant added notify owner
    """
    subject = pgettext('email', 'A participant has been added to your activity "{title}" 🎉')
    template = 'messages/participant_added_owner'
    context = {
        'title': 'activity.title',
        'participant_name': 'user.full_name'
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'Open your activity')

    def get_recipients(self):
        """activity owner"""
        return [self.obj.activity.owner]


class ParticipantRemovedOwnerNotification(TransitionMessage):
    """
    A participant removed notify owner
    """
    subject = pgettext('email', 'A participant has been removed from your activity "{title}"')
    template = 'messages/participant_removed_owner'
    context = {
        'title': 'activity.title',
        'participant_name': 'user.full_name'
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'Open your activity')

    def get_recipients(self):
        """activity owner"""
        return [self.obj.activity.owner]
