# -*- coding: utf-8 -*-
from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class ApplicantAcceptedMessage(TransitionMessage):
    subject = _('You have been accepted for the task {assignment_title}')
    template = 'messages/applicant_accepted'
    context = {
        'assignment_title': 'title'
    }


class ApplicantRejectedMessage(TransitionMessage):
    subject = _('You not been selected for the task {assignment_title}')
    template = 'messages/applicant_rejected'
    context = {
        'assignment_title': 'title'
    }


class AssignmentExpiredMessage(TransitionMessage):
    subject = _('Your task {assignment_title} has been closed')
    template = 'messages/assignment_expired'
    context = {
        'assignment_title': 'title'
    }


class AssignmentClosedMessage(TransitionMessage):
    subject = _('Your task {assignment_title} has been closed')
    template = 'messages/assignment_closed'
    context = {
        'assignment_title': 'title'
    }


class AssignmentCompletedMessage(TransitionMessage):
    subject = _(u'Your task {assignment_title} has been completed! 🎉')
    template = 'messages/assignment_completed'
    context = {
        'assignment_title': 'title'
    }


class AssignmentApplicationMessage(TransitionMessage):
    subject = _(u'Someone applied to your task {assignment_title}! 🙌')
    template = 'messages/assignment_application'
    context = {
        'assignment_title': 'activity.title'
    }

    def get_recipients(self):
        return [self.obj.activity.owner]


class AssignmentDateChanged(TransitionMessage):
    subject = _('The date and time for your task changed')
    template = 'messages/assignment_date_changed'

    def get_recipients(self):
        return [
            contribution.user for contribution
            in self.obj.contributions.filter(status='new')
        ]


class AssignmentReminderOnDate(TransitionMessage):
    subject = _('"{assigment_title}" will take place in 5 days!')
    template = 'messages/assignment_reminder_on_date'

    context = {
        'assignment_title': 'title'
    }

    def get_recipients(self):
        return [
            contribution.user for contribution
            in self.obj.contributions.filter(status='new')
        ]


class AssignmentReminderDeadline(TransitionMessage):
    subject = _('The deadline for your task "{assignment_title}" is getting close')
    template = 'messages/assignment_reminder_deadline'

    context = {
        'assignment_title': 'title'
    }

    def get_recipients(self):
        return [
            contribution.user for contribution
            in self.obj.contributions.filter(status='new')
        ]
