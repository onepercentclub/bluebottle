# -*- coding: utf-8 -*-
from bluebottle.assignments.models import Applicant, Assignment

from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class ApplicantAcceptedMessage(TransitionMessage):
    """
    Applicant has been accepted
    """
    subject = _('You have been accepted for the task "{assignment_title}"!')
    template = 'messages/applicant_accepted'
    model = Applicant
    context = {
        'assignment_title': 'activity.title'
    }

    def get_recipients(self):
        """the applicant"""
        return [self.obj.user]


class ApplicantRejectedMessage(TransitionMessage):
    """
    Applicant has been rejected
    """
    subject = _('You have not been selected for the task "{assignment_title}"')
    template = 'messages/applicant_rejected'
    model = Applicant
    context = {
        'assignment_title': 'activity.title'
    }

    def get_recipients(self):
        """the applicant"""
        return [self.obj.user]


class AssignmentExpiredMessage(TransitionMessage):
    """
    Task has expired. There where no sign-ups before the deadline to apply.
    """
    subject = _('Your task "{assignment_title}" has expired')
    template = 'messages/assignment_expired'
    model = Assignment
    context = {
        'assignment_title': 'title'
    }

    def get_recipients(self):
        """the organizer"""
        return [self.obj.owner]


class AssignmentCancelledMessage(TransitionMessage):
    subject = _('Your task "{assignment_title}" has been cancelled')
    template = 'messages/assignment_cancelled'
    model = Assignment
    context = {
        'assignment_title': 'title'
    }

    def get_recipients(self):
        """the organizer"""
        return [self.obj.owner]


class AssignmentRejectedMessage(TransitionMessage):
    subject = _('Your task "{assignment_title}" has been rejected')
    template = 'messages/assignment_rejected'
    model = Assignment
    context = {
        'assignment_title': 'title'
    }

    def get_recipients(self):
        """the organizer"""
        return [self.obj.owner]


class AssignmentClosedMessage(TransitionMessage):
    """
    Task rejected. The task has been rejected by an admin.
    """
    subject = _('Your task "{assignment_title}" has been closed')
    template = 'messages/assignment_closed'
    model = Assignment
    context = {
        'assignment_title': 'title'
    }

    def get_recipients(self):
        """the organizer"""
        return [self.obj.owner]


class AssignmentCompletedMessage(TransitionMessage):
    """
    Task completed. The task was completed successfully.
    """
    subject = _(u'Your task "{title}" has been successfully completed! 🎉')
    template = 'messages/assignment_completed'
    model = Assignment
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        """the organizer"""
        return [self.obj.owner]


class AssignmentApplicationMessage(TransitionMessage):
    """
    Someone applied to the task.
    """
    subject = _(u'Someone applied to your task "{assignment_title}"! 🙌')
    template = 'messages/assignment_application'
    model = Applicant
    context = {
        'assignment_title': 'activity.title'
    }

    def get_recipients(self):
        """the organizer"""
        return [self.obj.activity.owner]


class AssignmentDateChanged(TransitionMessage):
    """
    The date of the task changed.
    """
    subject = _('The date of your task "{assignment_title}" has been changed.')
    template = 'messages/assignment_date_changed'
    model = Assignment
    context = {
        'assignment_title': 'title'
    }

    def get_recipients(self):
        """users that applied to the task"""
        from bluebottle.assignments.models import Applicant
        return [
            contributor.user for contributor
            in self.obj.contributors.instance_of(Applicant).filter(status__in=('new', 'accepted', ))
        ]


class AssignmentDeadlineChanged(TransitionMessage):
    """
    The deadline of the task changed.
    """
    subject = _('The deadline for your task "{assignment_title}" has been changed.')
    template = 'messages/assignment_deadline_changed'
    model = Assignment
    context = {
        'assignment_title': 'title'
    }

    def get_recipients(self):
        """users that applied to the task"""
        from bluebottle.assignments.models import Applicant
        return [
            contributor.user for contributor
            in self.obj.contributors.instance_of(Applicant).filter(status__in=('new', 'accepted', ))
        ]


class AssignmentReminderOnDate(TransitionMessage):
    """
    Task takes place in 5 days.
    """

    subject = _('"{assignment_title}" will take place in 5 days!')
    template = 'messages/assignment_reminder_on_date'
    model = Assignment
    context = {
        'assignment_title': 'title'
    }
    send_once = True

    def get_recipients(self):
        """users that applied to the task"""
        from bluebottle.assignments.models import Applicant
        return [
            contributor.user for contributor
            in self.obj.contributors.instance_of(Applicant).filter(status__in=('new', 'accepted', ))
        ]


class AssignmentReminderDeadline(TransitionMessage):
    """
    Task deadline is in 5 days.
    """

    subject = _(
        'The deadline for your task "{assignment_title}" is getting close')
    template = 'messages/assignment_reminder_deadline'
    model = Assignment
    context = {
        'assignment_title': 'title'
    }
    send_once = True

    def get_recipients(self):
        """users that applied to the task"""
        from bluebottle.assignments.models import Applicant
        return [
            contributor.user for contributor
            in self.obj.contributors.instance_of(Applicant).filter(status__in=('new', 'accepted', ))
        ]
