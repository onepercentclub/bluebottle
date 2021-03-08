# -*- coding: utf-8 -*-
from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class DeedDateChangedNotification(TransitionMessage):

    subject = pgettext('email', 'The date for the activity "{title}" has changed')
    template = 'messages/deed_date_changed'

    context = {
        'title': 'title',
    }

    def get_context(self, recipient):
        context = super().get_context(recipient)
        if self.obj.start:
            context['start'] = self.obj.start.strftime('%x')
        else:
            context['start'] = pgettext('email', 'Today')

        if self.obj.end:
            context['end'] = self.obj.end.strftime('%x')
        else:
            context['end'] = pgettext('email', 'Runs indefinitely')
        return context

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participants that signed up"""
        return [
            participant.user for participant in self.obj.participants
        ]


class DeedReminderNotification(TransitionMessage):

    subject = pgettext('email', 'Your activity "{title}" will start tomorrow!')
    template = 'messages/deed_reminder'

    context = {
        'title': 'title',
    }

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    action_title = pgettext('email', 'Open your activity')

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]
