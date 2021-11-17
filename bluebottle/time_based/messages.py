# -*- coding: utf-8 -*-
from django.template import defaultfilters
from django.utils.timezone import get_current_timezone
from django.utils.translation import pgettext_lazy as pgettext
from pytz import timezone

from bluebottle.clients.utils import tenant_url
from bluebottle.notifications.messages import TransitionMessage
from bluebottle.time_based.models import (
    DateParticipant, SlotParticipant,
    PeriodParticipant, DateActivitySlot
)


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


class TimeBasedInfoMixin(object):

    def get_context(self, recipient):
        context = super().get_context(recipient)
        if isinstance(self.obj, (DateParticipant, PeriodParticipant)):
            participant = self.obj
        elif isinstance(self.obj, DateActivitySlot):
            participant = self.obj.activity.participants.get(user=recipient)
        elif isinstance(self.obj, SlotParticipant):
            participant = self.obj.participant
        else:
            participant = self.obj.participants.get(user=recipient)

        if isinstance(participant, DateParticipant):
            slots = []
            for slot_participant in participant.slot_participants.filter(
                status='registered'
            ):
                slots.append(get_slot_info(slot_participant.slot))

            context.update({'slots': slots})
        elif isinstance(participant, PeriodParticipant):
            context.update({
                'start': participant.activity.start,
                'end': participant.activity.deadline,
            })
        return context


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

    def get_context(self, recipient):
        context = super().get_context(recipient)

        if self.obj.start:
            context['start'] = pgettext(
                'emai', 'on {start}'
            ).format(start=defaultfilters.date(self.obj.start))
        else:
            context['start'] = pgettext('emai', 'immediately')

        if self.obj.deadline:
            context['end'] = pgettext(
                'emai', 'ends on {end}'
            ).format(end=defaultfilters.date(self.obj.deadline))
        else:
            context['end'] = pgettext('emai', 'runs indefinitely')

        return context


class ReminderSingleDateNotification(TimeBasedInfoMixin, TransitionMessage):
    """
    Reminder notification for a single date activity
    """
    subject = pgettext('email', 'The activity "{title}" will take place in a few days!')
    template = 'messages/reminder_single_date'
    send_once = True
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


class ChangedSingleDateNotification(TimeBasedInfoMixin, TransitionMessage):
    """
    Notification when slot details (date, time or location) changed for a single date activity
    """
    subject = pgettext('email', 'The details of activity "{title}" have changed')
    template = 'messages/changed_single_date'
    context = {
        'title': 'activity.title',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.activity.accepted_participants
        ]


class ChangedMultipleDateNotification(TimeBasedInfoMixin, TransitionMessage):
    """
    Notification when slot details (date, time or location) changed for a single date activity
    """
    subject = pgettext('email', 'The details of activity "{title}" have changed')
    template = 'messages/changed_multiple_dates'
    context = {
        'title': 'activity.title',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.activity.accepted_participants
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
        if self.obj.user:
            return [self.obj.user]
        else:
            return []


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
        if self.obj.user:
            return [self.obj.activity.owner]
        else:
            return []


class ParticipantNotification(TimeBasedInfoMixin, TransitionMessage):
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


class ParticipantJoinedNotification(TimeBasedInfoMixin, TransitionMessage):
    """
    The participant joined
    """
    subject = pgettext('email', 'You have joined the activity "{title}"')
    template = 'messages/participant_joined'
    context = {
        'title': 'activity.title',
    }

    delay = 60

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class ParticipantChangedNotification(TimeBasedInfoMixin, TransitionMessage):
    """
    The participant withdrew or applied to a slot when already applied to other slots
    """
    subject = pgettext('email', 'You have changed your application on the activity "{title}"')
    template = 'messages/participant_changed'
    context = {
        'title': 'activity.title',
    }

    delay = 60

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    @property
    def task_id(self):
        return f'{self.__class__.__name__}-{self.obj.participant.id}'

    def get_recipients(self):
        """participant"""
        joined_message = ParticipantJoinedNotification(self.obj.participant)
        applied_message = ParticipantAppliedNotification(self.obj.participant)
        changed_message = ParticipantChangedNotification(self.obj)

        participant = DateParticipant.objects.get(pk=self.obj.participant.pk)

        if (
            participant.status == 'withdrawn' or
            joined_message.is_delayed or
            changed_message.is_delayed or applied_message.is_delayed
        ):
            return []

        return [self.obj.participant.user]


class ParticipantAppliedNotification(TimeBasedInfoMixin, TransitionMessage):
    """
    The participant joined
    """
    subject = pgettext('email', 'You have applied to the activity "{title}"')
    template = 'messages/participant_applied'
    context = {
        'title': 'activity.title',
    }
    delay = 60

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class ParticipantAcceptedNotification(TimeBasedInfoMixin, TransitionMessage):
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
        if self.obj.user:
            return [self.obj.activity.owner]
        else:
            return []


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
