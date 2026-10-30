from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.activities.messages.base import ThankYouMessageMixin
from bluebottle.notifications.messages import TransitionMessage


class ThankYouNotification(ThankYouMessageMixin, TransitionMessage):
    subject = pgettext('platform-email', 'Thank you for participating in the activity "{title}"')
    template = 'messages/thank_you/participant'
    send_once = True
    append_custom_message = True
    context = {
        'title': 'activity.title',
    }
    action_title = pgettext('platform-email', 'View activity')

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    class Meta:
        abstract = True


class DateParticipantThankYouNotification(ThankYouNotification):
    pass


class ScheduleParticipantThankYouNotification(ThankYouNotification):
    pass


class TeamThankYouNotification(ThankYouNotification):
    def get_thank_you_recipients(self):
        """team captain"""
        return [self.obj.user]


class RegistrationActivityThankYouNotification(ThankYouNotification):
    context = {
        'title': 'title',
    }

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    def get_thank_you_recipients(self):
        """participants"""
        return list(dict.fromkeys(
            participant.user for participant in
            self.obj.participants.filter(status__in=('accepted', 'succeeded')).select_related('user')
            if participant.user
        ))


class PeriodicActivityThankYouNotification(RegistrationActivityThankYouNotification):
    def get_thank_you_recipients(self):
        """participants"""
        return list(dict.fromkeys(
            registration.user for registration in
            self.obj.registrations.filter(status__in=('accepted', 'stopped')).select_related('user')
            if registration.user
        ))
