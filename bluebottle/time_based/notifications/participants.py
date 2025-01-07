from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage
from bluebottle.time_based.messages import get_slot_info


class ManagerParticipantNotification(TransitionMessage):
    context = {
        'title': 'activity.title',
        'name': 'user.full_name',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'Open your activity')

    def get_recipients(self):
        """manager"""
        return [self.obj.activity.owner]


class ManagerParticipantRemovedNotification(ManagerParticipantNotification):
    """
    A participant removed notify owner
    """
    subject = pgettext('email', 'A participant has been removed from your activity "{title}"')
    template = 'messages/participants/manager_participant_removed'


class ManagerParticipantWithdrewNotification(ManagerParticipantNotification):
    """
    A participant withdrew from your activity
    """
    subject = pgettext('email', 'A participant has withdrawn from your activity "{title}"')
    template = 'messages/participants/manager_participant_withdrew'


class UserParticipantNotification(TransitionMessage):
    context = {
        'title': 'activity.title',
        'name': 'user.full_name',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class UserParticipantRemovedNotification(UserParticipantNotification):
    """
    The participant was removed from the activity
    """
    subject = pgettext('email', 'You have been removed as participant for the activity "{title}"')
    template = 'messages/participants/user_participant_removed'


class UserParticipantWithdrewNotification(UserParticipantNotification):
    """
    The participant was removed from the activity
    """
    subject = pgettext('email', 'You have withdrawn from the activity "{title}"')
    template = 'messages/participants/user_participant_withdrew'


class UserScheduledNotification(UserParticipantNotification):
    """
    The participant was removed from the activity
    """
    subject = pgettext('email', 'You have been scheduled for the activity "{title}"')
    template = 'messages/participants/user_participant_scheduled'

    def get_context(self, recipient):
        context = super(UserScheduledNotification, self).get_context(recipient)
        if self.obj.slot and self.obj.slot.start:
            context['slot'] = get_slot_info(self.obj.slot)
        return context
