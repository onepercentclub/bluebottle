# -*- coding: utf-8 -*-

from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class ManagerRegistrationNotification(TransitionMessage):
    context = {
        'title': 'activity.title',
        'applicant_name': 'user.full_name',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'Open your activity')

    def get_recipients(self):
        """activity owner"""
        return [self.obj.activity.owner]


class ManagerRegistrationCreatedReviewNotification(ManagerRegistrationNotification):
    subject = pgettext('email', 'You have a new application for your activity "{title}"')
    template = 'messages/registration/manager_registration_created_review'


class ManagerRegistrationCreatedNotification(ManagerRegistrationNotification):
    subject = pgettext('email', 'You have a new participant for your activity "{title}"')
    template = 'messages/registration/manager_registration_created'


class UserRegistrationNotification(TransitionMessage):
    context = {
        'title': 'activity.title',
        'applicant_name': 'user.full_name',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """applicant"""
        return [self.obj.user]


class UserRegistrationAcceptedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have been selected for the activity "{title}"')
    template = 'messages/registration/user_accepted'


class UserRegistrationRejectedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have not been selected for the activity "{title}"')
    template = 'messages/registration/user_rejected'


class UserAppliedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have applied to the activity "{title}"')
    template = 'messages/registration/user_applied'
