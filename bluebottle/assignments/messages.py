# -*- coding: utf-8 -*-
from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class ApplicantAcceptedMessage(TransitionMessage):
    subject = _('You have been accepted for the task "{assignment_title}"!')
    template = 'messages/applicant_accepted'
    context = {
        'assignment_title': 'activity.title'
    }

    def get_recipients(self):
        """the applicant"""
        return [self.obj.user]


class ApplicantRejectedMessage(TransitionMessage):
    subject = _('You have not been selected for the task "{assignment_title}"')
    template = 'messages/applicant_rejected'
    context = {
        'assignment_title': 'activity.title'
    }

    def get_recipients(self):
        """the applicant"""
        return [self.obj.user]


class AssignmentExpiredMessage(TransitionMessage):
    subject = _('Your task "{assignment_title}" has expired')
    template = 'messages/assignment_expired'
    context = {
        'assignment_title': 'title'
    }

    def get_recipients(self):
        """the organizer"""
        return [self.obj.owner]


class AssignmentCancelledMessage(TransitionMessage):
    subject = _('Your task "{assignment_title}" has been cancelled')
    template = 'messages/assignment_cancelled'
    context = {
        'assignment_title': 'title'
    }

    def get_recipients(self):
        """the organizer"""
        return [self.obj.owner]


class AssignmentRejectedMessage(TransitionMessage):
    subject = _('Your task "{assignment_title}" has been rejected')
    template = 'messages/assignment_rejected'
    context = {
        'assignment_title': 'title'
    }

    def get_recipients(self):
        """the organizer"""
        return [self.obj.owner]


class AssignmentClosedMessage(TransitionMessage):
    subject = _('Your task "{assignment_title}" has been closed')
    template = 'messages/assignment_closed'
    context = {
        'assignment_title': 'title'
    }

    def get_recipients(self):
        """the organizer"""
        return [self.obj.owner]


class AssignmentCompletedMessage(TransitionMessage):
    subject = _(u'Your task "{title}" has been successfully completed! 🎉')
    template = 'messages/assignment_completed'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the organizer"""
        return [self.obj.owner]


class AssignmentApplicationMessage(TransitionMessage):
    subject = _(u'Someone applied to your task "{assignment_title}"! 🙌')
    template = 'messages/assignment_application'
    context = {
        'assignment_title': 'activity.title'
    }

    def get_recipients(self):
        """the organizer"""
        return [self.obj.activity.owner]


class AssignmentDateChanged(TransitionMessage):
    subject = _('The date of your task "{assignment_title}" has been changed.')
    template = 'messages/assignment_date_changed'
    context = {
        'assignment_title': 'title'
    }

    def get_recipients(self):
        """users that applied to the task"""
        from bluebottle.assignments.models import Applicant
        return [
            contribution.user for contribution
            in self.obj.contributions.instance_of(Applicant).filter(status__in=('new', 'accepted', ))
        ]


class AssignmentDeadlineChanged(TransitionMessage):
    subject = _('The deadline for your task "{assignment_title}" has been changed.')
    template = 'messages/assignment_deadline_changed'
    context = {
        'assignment_title': 'title'
    }

    def get_recipients(self):
        """users that applied to the task"""
        from bluebottle.assignments.models import Applicant
        return [
            contribution.user for contribution
            in self.obj.contributions.instance_of(Applicant).filter(status__in=('new', 'accepted', ))
        ]


class AssignmentReminderOnDate(TransitionMessage):
    subject = _('"{assignment_title}" will take place in 5 days!')
    template = 'messages/assignment_reminder_on_date'
    context = {
        'assignment_title': 'title'
    }
    send_once = True

    def get_recipients(self):
        """users that applied to the task"""
        from bluebottle.assignments.models import Applicant
        return [
            contribution.user for contribution
            in self.obj.contributions.instance_of(Applicant).filter(status__in=('new', 'accepted', ))
        ]


class AssignmentReminderDeadline(TransitionMessage):
    subject = _(
        'The deadline for your task "{assignment_title}" is getting close')
    template = 'messages/assignment_reminder_deadline'
    context = {
        'assignment_title': 'title'
    }
    send_once = True

    def get_recipients(self):
        """users that applied to the task"""
        from bluebottle.assignments.models import Applicant
        return [
            contribution.user for contribution
            in self.obj.contributions.instance_of(Applicant).filter(status__in=('new', 'accepted', ))
        ]
