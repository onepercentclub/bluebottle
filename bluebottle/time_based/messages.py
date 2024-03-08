# -*- coding: utf-8 -*-

from django.contrib.admin.options import get_content_type_for_model
from django.template import defaultfilters
from django.utils.timezone import get_current_timezone
from django.utils.translation import pgettext_lazy as pgettext
from pytz import timezone

from bluebottle.clients.utils import tenant_url
from bluebottle.notifications.messages import TransitionMessage
from bluebottle.notifications.models import Message
from bluebottle.time_based.models import (
    DateParticipant, SlotParticipant,
    PeriodParticipant, DateActivitySlot, PeriodActivity
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


class ReminderSlotNotification(TimeBasedInfoMixin, TransitionMessage):
    """
    Reminder notification for a date activity slot
    """
    subject = pgettext('email', 'The activity "{title}" will take place tomorrow!')
    template = 'messages/reminder_slot'
    send_once = True

    context = {
        'title': 'activity.title',
    }

    def already_send(self, recipient):
        return Message.objects.filter(
            template=self.get_template(),
            recipient=recipient,
            content_type=get_content_type_for_model(self.obj),
            object_id=self.obj.id
        ).exists()

    def get_context(self, recipient):
        context = super().get_context(recipient)
        slots = [self.obj]
        context['slots'] = [get_slot_info(slot) for slot in slots]
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


class ReminderTeamSlotNotification(TransitionMessage):
    """
    Reminder notification for a team activity slot
    """
    subject = pgettext('email', 'The team activity "{title}" will take place in a few days!')
    template = 'messages/reminder_team_slot'
    send_once = True

    context = {
        'title': 'activity.title',
        'team_name': 'team',
        'start': 'start',
        'duration': 'duration',
        'end': 'end',
        'timezone': 'timezone',
        'location': 'location',
    }

    def already_send(self, recipient):
        return Message.objects.filter(
            template=self.get_template(),
            recipient=recipient,
            content_type=get_content_type_for_model(self.obj),
            object_id=self.obj.id
        ).count() > 0

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.team.accepted_participants
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

    def get_event_data(self, recipient=None):
        return self.obj.event_data

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

    def get_event_data(self, recipient=None):
        slots = self.obj.activity.slots.filter(
            slot_participants__participant__user=recipient,
            slot_participants__participant__status='accepted',
            slot_participants__status='registered',
        ).all()
        return [slot.event_data for slot in slots]

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participants that signed up"""
        return [
            slot_participant.participant.user for slot_participant
            in self.obj.slot_participants.all()
            if (
                slot_participant.status == 'registered' and
                slot_participant.participant.status == 'accepted'
            )
        ]


class TeamSlotChangedNotification(TransitionMessage):
    """
    Notification when slot details (date, time or location) changed for a team activity
    """
    subject = pgettext('email', 'The details of the team activity "{title}" have changed')
    template = 'messages/changed_team_date'
    context = {
        'title': 'activity.title',
        'team_name': 'team',
        'start': 'start',
        'duration': 'duration',
        'end': 'end',
        'is_online': 'activity.is_online',
        'location': 'location.formatted_address',
        'timezone': 'timezone',
    }

    def get_event_data(self, recipient=None):
        return self.obj.event_data

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """team members"""
        return [
            participant.user for participant in self.obj.team.accepted_participants
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

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participant"""
        if self.obj.user:
            return [self.obj.user]
        else:
            return []


class TeamParticipantAddedNotification(TransitionMessage):
    """
    A participant was added to a team manually (through back-office)
    """
    subject = pgettext('email', 'You have been added to a team for "{title}" 🎉')
    template = 'messages/team_participant_added'
    context = {
        'title': 'activity.title',
        'team_name': 'team.name',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

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
        'question': 'activity.review_title',
        'answer': 'motivation'
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
        'applicant_name': 'user.full_name',
        'question': 'activity.review_title',
        'answer': 'motivation'
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

    def get_event_data(self, recipient=None):
        if isinstance(self.obj.activity, PeriodActivity):
            # TODO: Come up with calendar events once we've added slots to period activities too
            return []
        slots = self.obj.activity.slots.filter(
            slot_participants__participant__user=recipient,
            slot_participants__participant__status='accepted',
            slot_participants__status='registered',
        ).all()
        return [slot.event_data for slot in slots]

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class TeamParticipantJoinedNotification(TransitionMessage):
    """
    The participant joined
    """
    subject = pgettext('email', 'You have registered your team for "{title}"')
    template = 'messages/team_participant_joined'
    context = {
        'title': 'activity.title',
    }

    delay = 60

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """team captain"""
        return [self.obj.owner]


class ParticipantChangedNotification(TimeBasedInfoMixin, TransitionMessage):
    """
    The participant withdrew or applied to a slot when already applied to other slots
    """
    subject = pgettext('email', 'You have changed your application on the activity "{title}"')
    template = 'messages/participant_changed'
    context = {
        'title': 'activity.title',
    }

    delay = 55

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


class TeamParticipantAppliedNotification(TimeBasedInfoMixin, TransitionMessage):
    """
    The participant joined as a team joined
    """
    subject = pgettext('email', 'You have registered your team for "{title}"')
    template = 'messages/team_participant_applied'
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


class TeamMemberJoinedNotification(TimeBasedInfoMixin, TransitionMessage):
    """
    The participant joined as a team joined
    """
    subject = pgettext('email', 'You have joined {team_name} for "{title}"')
    template = 'messages/team_member_joined'
    context = {
        'title': 'activity.title',
        'team_name': 'team.name'
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

    def get_event_data(self, recipient=None):
        if isinstance(self.obj.activity, PeriodActivity):
            # TODO: Come up with calendar events once we've added slots to period activities too
            return []
        return [slot_participant.slot.event_data for slot_participant in self.obj.slot_participants.all()]

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class ParticipantRejectedNotification(TransitionMessage):
    """
    The participant got rejected after review
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


class TeamParticipantRemovedNotification(TransitionMessage):
    """
    The participant was removed from the activity
    """
    subject = pgettext('email', 'Your team participation in ‘{title}’ has been cancelled')
    template = 'messages/team_participant_removed'
    context = {
        'title': 'activity.title',
        'team_name': 'team.name',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

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


class ManagerSlotParticipantWithdrewNotification(TransitionMessage):
    """
    A slot participant withdrew from a time slot for your activity
    """
    subject = pgettext('email', 'A participant has withdrawn from a time slot for your activity "{title}"')
    template = 'messages/manager/slot_participant_withdrew'
    context = {
        'title': 'activity.title',
        'participant_name': 'participant.user.full_name',
    }

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context['slot'] = get_slot_info(self.obj.slot)
        return context

    @property
    def action_link(self):
        return self.obj.slot.activity.get_absolute_url()

    action_title = pgettext('email', 'Open your activity')

    def get_recipients(self):
        """activity owner"""
        return [self.obj.slot.activity.owner]


class ManagerSlotParticipantRegisteredNotification(TransitionMessage):
    """
    A slot participant registered from a time slot for your activity
    """
    subject = pgettext('email', 'A participant has registered for a time slot for your activity "{title}"')
    template = 'messages/manager/slot_participant_registered'
    context = {
        'title': 'activity.title',
        'participant_name': 'participant.user.full_name',
        'answer': 'participant.motivation',
        'question': 'activity.review_title'
    }

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context['slot'] = get_slot_info(self.obj.slot)
        return context

    @property
    def action_link(self):
        return self.obj.slot.activity.get_absolute_url()

    action_title = pgettext('email', 'View your activity')

    def get_recipients(self):
        """activity owner"""

        return [self.obj.slot.activity.owner]


class ParticipantSlotParticipantRegisteredNotification(TransitionMessage):
    """
    Slot participant registered for a time slot for an activity
    """
    subject = pgettext('email', 'You\'ve registered for a time slot for the activity "{title}"')
    template = 'messages/participant/slot_participant_registered'
    context = {
        'title': 'activity.title',
        'participant_name': 'participant.user.full_name',
    }

    def get_event_data(self, recipient):
        return self.obj.slot.event_data

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context['slot'] = get_slot_info(self.obj.slot)
        return context

    @property
    def action_link(self):
        return self.obj.slot.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participant"""

        return [self.obj.participant.user]


class ManagerParticipantAddedOwnerNotification(TransitionMessage):
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


class SlotCancelledNotification(TransitionMessage):
    """
    The activity slot got cancelled
    """
    subject = pgettext('email', 'A slot for your activity "{title}" has been cancelled')
    template = 'messages/slot_cancelled'

    context = {
        'title': 'activity.title',
    }

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context['slots'] = [get_slot_info(self.obj)]
        return context

    def get_recipients(self):
        """participants that signed up"""
        return [
            self.obj.activity.owner
        ] + [
            slot_participant.participant.user for slot_participant
            in self.obj.slot_participants.all()
            if (
                slot_participant.status == 'registered' and
                slot_participant.participant.status == 'accepted'
            )
        ]

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'Open your activity')
