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
    subject = pgettext('email', 'You have a new application for your activity "{title}" 🎉')
    template = 'messages/registrations/manager_registration_created_review'


class ManagerRegistrationCreatedNotification(ManagerRegistrationNotification):
    subject = pgettext('email', 'You have a new participant for your activity "{title}" 🎉')
    template = 'messages/registrations/manager_registration_created'


class UserRegistrationNotification(TransitionMessage):
    context = {
        'title': 'activity.title',
        'applicant_name': 'user.full_name',
    }

    def get_context(self, recipient):
        context = super(UserRegistrationNotification, self).get_context(recipient)
        return context

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """applicant"""
        return [self.obj.user]


class UserRegistrationAcceptedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have been selected for the activity "{title}"')
    template = 'messages/registrations/user_accepted'


class UserRegistrationRejectedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have not been selected for the activity "{title}"')
    template = 'messages/registrations/user_rejected'


class UserRegistrationStoppedNotification(UserRegistrationNotification):
    subject = pgettext(
        "email", 'Your contribution to the activity "{title}" has been stopped'
    )
    template = "messages/registrations/user_stopped"


class UserRegistrationRestartedNotification(UserRegistrationNotification):
    subject = pgettext(
        "email", 'Your contribution to the activity "{title}" has been restarted'
    )
    template = "messages/registrations/user_restarted"


class UserAppliedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have applied to the activity "{title}"')
    template = 'messages/registrations/user_applied'


class UserJoinedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have joined the activity "{title}"')
    template = 'messages/registrations/user_joined'