# -*- coding: utf-8 -*-
from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class DateChanged(TransitionMessage):
    subject = _('The date and time for your activity "{title}" changed')
    template = 'messages/date_changed'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """participants that signed up"""
        return [
            application.user for application in self.obj.accepted_applications
        ]


class DeadlineChanged(TransitionMessage):
    subject = _('The deadline for your activity "{title}" changed')
    template = 'messages/deadline_changed'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """participants that signed up"""
        return [
            application.user for application in self.obj.accepted_applications
        ]
