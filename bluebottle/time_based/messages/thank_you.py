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

    def get_thank_you_recipients(self):
        """participant"""
        return [self.obj.user]


class DateParticipantThankYouNotification(ThankYouNotification):
    pass


class ScheduleParticipantThankYouNotification(ThankYouNotification):
    def get_thank_you_recipients(self):
        """participant with a scheduled slot"""
        if not (self.obj.slot and self.obj.slot.start):
            return []
        return [self.obj.user]


class TeamThankYouNotification(ThankYouNotification):
    """
    Sent to the team captain only. Team members don't get a thank you email.
    """
    pass


class RegistrationActivityThankYouNotification(ThankYouNotification):
    context = {
        'title': 'title',
    }

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    def get_thank_you_recipients(self):
        """participants with a succeeded contribution"""
        return self.get_succeeded_contributors(self.obj)


class PeriodicActivityThankYouNotification(RegistrationActivityThankYouNotification):
    pass
