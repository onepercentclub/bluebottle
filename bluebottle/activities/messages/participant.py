from urllib.parse import urlparse

from django.core.signing import TimestampSigner
from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class InactiveParticipantAddedNotification(TransitionMessage):
    subject = pgettext('email', "You have been added to the activity {title}")
    template = 'messages/inactive-participant-added'

    context = {
        'title': 'activity.title',
    }

    @property
    def action_link(self):
        user = self.obj.user

        token = TimestampSigner().sign(user.pk)
        activity_url = urlparse(self.obj.activity.get_absolute_url()).path[3:]

        url = f'/auth/confirm/?token={token}&email={user.email}&url={activity_url}'
        return url

    def get_recipients(self):
        """Participant"""
        return [self.obj.user]
