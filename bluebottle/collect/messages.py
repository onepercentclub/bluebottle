# -*- coding: utf-8 -*-
from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class CollectActivityDateChangedNotification(TransitionMessage):

    subject = pgettext('platform-email', 'The date for the activity "{title}" has changed')
    template = 'messages/collect_activity_date_changed'

    context = {
        'title': 'title',
    }

    def get_context(self, recipient):
        context = super().get_context(recipient)
        if self.obj.start:
            context['start'] = self.obj.start.strftime('%x')
        else:
            context['start'] = pgettext('platform-email', 'Today')

        if self.obj.end:
            context['end'] = self.obj.end.strftime('%x')
        else:
            context['end'] = pgettext('platform-email', 'Runs indefinitely')
        return context

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    action_title = pgettext('platform-email', 'View activity')

    def get_recipients(self):
        """contributors that signed up"""
        return [
            contributor.user for contributor in self.obj.active_contributors.all()
        ]


class CollectActivityReminderNotification(TransitionMessage):

    subject = pgettext('platform-email', 'Your activity "{title}" will start tomorrow!')
    template = 'messages/collect_activity_reminder'
    send_once = True

    context = {
        'title': 'title',
    }

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    action_title = pgettext('platform-email', 'Open your activity')

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ParticipantJoinedNotification(TransitionMessage):
    """
    The participant joined
    """
    subject = pgettext('platform-email', 'You have joined the activity "{title}"')
    template = 'messages/collect_participant_joined'
    context = {
        'title': 'activity.title',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('platform-email', 'View activity')

    def get_context(self, recipient):
        context = super().get_context(recipient)
        if self.obj.activity.start:
            context['start'] = self.obj.activity.start.strftime('%x')

        if self.obj.activity.end:
            context['end'] = self.obj.activity.end.strftime('%x')

        return context

    def get_recipients(self):
        """participant"""
        return [self.obj.user]
