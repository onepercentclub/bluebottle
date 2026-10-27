from gettext import pgettext

from bluebottle.notifications.messages import TransitionMessage
from bluebottle.utils.utils import get_current_host, get_current_language


class BaseParticipantNotification(TransitionMessage):
    link_to_overview = False

    @property
    def action_link(self):
        if self.link_to_overview:
            if self.link_to_overview:
                domain = get_current_host()
                language = get_current_language()
                return "{}/{}/activities/list".format(
                    domain, language
                )
        return self.obj.activity.get_absolute_url()

    @property
    def action_title(self):
        if self.link_to_overview:
            return pgettext('platform-email', 'View all activities')
        return pgettext('platform-email', 'View activity')

    def get_recipients(self):
        """participant"""
        return [self.obj.user]

    class Meta:
        abstract = True
