# -*- coding: utf-8 -*-

from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage
from bluebottle.time_based.models import PeriodicActivity, DeadlineActivity
from bluebottle.utils.widgets import duration_to_hours


class ManagerRegistrationNotification(TransitionMessage):
    context = {
        'title': 'activity.title',
        'applicant_name': 'user.full_name',
        'team_name': 'team.name',
        'captain_email': 'team.user.email',
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


class ManagerRegistrationStoppedNotification(ManagerRegistrationNotification):
    subject = pgettext("email", 'A participant for your activity "{title}" has stopped')
    template = "messages/registrations/manager_registration_stopped"


class ManagerRegistrationRestartedNotification(ManagerRegistrationNotification):
    subject = pgettext(
        "email", 'A participant for your activity "{title}" has restarted'
    )
    template = "messages/registrations/manager_registration_restarted"


class UserRegistrationNotification(TransitionMessage):
    context = {
        'title': 'activity.title',
        'applicant_name': 'user.full_name',
    }

    def get_context(self, recipient):
        context = super(UserRegistrationNotification, self).get_context(recipient)
        if isinstance(self.obj.activity, PeriodicActivity):
            context['start'] = self.obj.activity.start
            context['end'] = self.obj.activity.deadline
            context['duration'] = duration_to_hours(self.obj.activity.duration)
            if self.obj.activity.period == 'days':
                context['period'] = _('day')
            if self.obj.activity.period == 'weeks':
                context['period'] = _('week')
            if self.obj.activity.period == 'months':
                context['period'] = _('month')
        if isinstance(self.obj.activity, DeadlineActivity):
            context['start'] = self.obj.activity.start
            context['end'] = self.obj.activity.deadline
            context['duration'] = duration_to_hours(self.obj.activity.duration)

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


class UserTeamRegistrationAcceptedNotification(UserRegistrationNotification):
    subject = pgettext(
        "email", 'Your team has been selected for the activity "{title}"'
    )
    template = "messages/registrations/team_accepted"


class UserRegistrationRejectedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have not been selected for the activity "{title}"')
    template = 'messages/registrations/user_rejected'


class UserRegistrationRemovedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have been removed from the activity "{title}"')
    template = 'messages/registrations/user_removed'


class UserTeamRegistrationRejectedNotification(UserRegistrationNotification):
    subject = pgettext(
        "email", 'Your team has not been selected for the activity "{title}"'
    )
    template = "messages/registrations/team_rejected"


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

    def get_context(self, recipient):
        context = super(UserRegistrationNotification, self).get_context(recipient)
        context['duration'] = duration_to_hours(self.obj.activity.duration)
        if self.obj.activity.period == 'days':
            context['period'] = pgettext('email', 'day')
        if self.obj.activity.period == 'weeks':
            context['period'] = pgettext('email', 'week')
        if self.obj.activity.period == 'months':
            context['period'] = pgettext('email', 'months')
        return context


class DeadlineUserAppliedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have applied to the activity "{title}"')
    template = 'messages/registrations/deadline/user_applied'


class DeadlineUserJoinedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have joined the activity "{title}"')
    template = 'messages/registrations/deadline/user_joined'


class ScheduleUserAppliedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have applied to the activity "{title}"')
    template = 'messages/registrations/schedule/user_applied'


class ScheduleUserJoinedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have joined the activity "{title}"')
    template = 'messages/registrations/schedule/user_joined'


class TeamScheduleUserAppliedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have applied to the activity "{title}"')
    template = 'messages/registrations/schedule/team_applied'


class TeamScheduleUserJoinedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have joined the activity "{title}"')
    template = 'messages/registrations/schedule/team_joined'


class PeriodicUserAppliedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have applied to the activity "{title}"')
    template = 'messages/registrations/periodic/user_applied'


class PeriodicUserJoinedNotification(UserRegistrationNotification):
    subject = pgettext('email', 'You have joined the activity "{title}"')
    template = 'messages/registrations/periodic/user_joined'


class ManagerTeamRegistrationCreatedReviewNotification(ManagerRegistrationNotification):
    subject = pgettext("email", 'A new team has applied to your activity "{title}" 🎉')
    template = "messages/registrations/manager_team_registration_created_review"


class ManagerTeamRegistrationCreatedNotification(ManagerRegistrationNotification):
    subject = pgettext("email", 'You have a new team for your activity "{title}" 🎉')
    template = "messages/registrations/manager_team_registration_created"


class TeamAppliedNotification(UserRegistrationNotification):
    subject = pgettext("email", 'You have registered your team on "{site_name}"')
    template = "messages/registrations/team_applied"


class TeamJoinedNotification(UserRegistrationNotification):
    subject = pgettext("email", 'You have registered your team on "{site_name}"')
    template = "messages/registrations/team_joined"
