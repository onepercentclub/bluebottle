# -*- coding: utf-8 -*-
from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class DateChanged(TransitionMessage):
    subject = _('The date and time for your activity "{title}" has changed')
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


class ActivitySucceededNotification(TransitionMessage):
    subject = _('Your activity "{title}" has succeeded 🎉')
    template = 'messages/activity_succeeded'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ActivitySucceededManuallyNotification(TransitionMessage):
    subject = _('The activity "{title}" has succeeded 🎉')
    template = 'messages/activity_succeeded_manually'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """participants that signed up"""
        return [
            application.user for application in self.obj.accepted_applications
        ]


class ActivityRejectedNotification(TransitionMessage):
    subject = _('Your activity "{title}" has been rejected')
    template = 'messages/activity_rejected'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ActivityCancelledNotification(TransitionMessage):
    subject = _('Your activity "{title}" has been cancelled')
    template = 'messages/activity_cancelled'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ActivityExpiredNotification(TransitionMessage):
    subject = _('The registration deadline for your activity "{title}" has expired')
    template = 'messages/activity_expired'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ApplicationAddedNotification(TransitionMessage):
    subject = _('You have been added to the activity "{title}" 🎉')
    template = 'messages/application_added'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """activity owner"""
        if self.options.get('user') != self.obj.user:
            return [self.obj.user]
        else:
            return []


class ApplicationCreatedNotification(TransitionMessage):
    subject = _('You have a new application for your activity "{title}" 🎉')
    template = 'messages/application_created'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.activity.owner]


class NewApplicationNotification(TransitionMessage):
    subject = _('A new participant has joined your activity "{title}" 🎉')
    template = 'messages/new_application'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.activity.owner]


class ApplicationAcceptedNotification(TransitionMessage):
    subject = _('You have been selected for the activity "{title}" 🎉')
    template = 'messages/application_accepted'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.user]


class ApplicationRejectedNotification(TransitionMessage):
    subject = _('You have not been selected for the activity "{title}"')
    template = 'messages/application_rejected'
    context = {
        'title': 'activity.title'
    }

    def get_recipients(self):
        """activity owner"""
        return [self.obj.user]
