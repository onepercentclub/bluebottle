# -*- coding: utf-8 -*-
from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class ApplicantAcceptedMessage(TransitionMessage):
    subject = _('You have been accepted for the assignment!')
    template = 'messages/applicant_accepted'


class ApplicantRejectedMessage(TransitionMessage):
    subject = _('You not been selected for the assignment')
    template = 'messages/applicant_rejected'


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
