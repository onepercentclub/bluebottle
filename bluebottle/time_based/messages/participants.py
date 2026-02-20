from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.initiatives.models import InitiativePlatformSettings
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

    action_title = pgettext('platform-email', 'Open your activity')

    def get_recipients(self):
        """manager"""
        return [self.obj.activity.owner]

    class Meta:
        abstract = True


class ManagerParticipantRemovedNotification(ManagerParticipantNotification):
    """
    A participant removed notify owner
    """
    subject = pgettext('platform-email', 'A participant has been removed from your activity "{title}"')
    template = 'messages/participants/manager_participant_removed'


class ManagerParticipantWithdrewNotification(ManagerParticipantNotification):
    """
    A participant withdrew from your activity
    """
    subject = pgettext('platform-email', 'A participant has withdrawn from your activity "{title}"')
    template = 'messages/participants/manager_participant_withdrew'


class UserParticipantNotification(TransitionMessage):
    context = {
        'title': 'activity.title',
        'name': 'user.full_name',
        'review_link': 'activity.review_link',
    }

    def get_context(self, recipient):
        context = super(UserParticipantNotification, self).get_context(recipient)
        settings = InitiativePlatformSettings.load()
        context['hour_registration'] = (
            settings.hour_registration != 'none'
            and self.obj.activity.hour_registration_data
            or settings.hour_registration_data
        )
        return context

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('platform-email', 'View activity')

    def get_recipients(self):
        """participant"""
        return [self.obj.user]

    class Meta:
        abstract = True


class UserParticipantRemovedNotification(UserParticipantNotification):
    """
    The participant was removed from the activity
    """
    subject = pgettext('platform-email', 'You have been removed as participant for the activity "{title}"')
    template = 'messages/participants/user_participant_removed'


class UserParticipantWithdrewNotification(UserParticipantNotification):
    """
    The participant was removed from the activity
    """
    subject = pgettext('platform-email', 'You have withdrawn from the activity "{title}"')
    template = 'messages/participants/user_participant_withdrew'


class UserDateParticipantWithdrewNotification(UserParticipantNotification):
    """
    The participant was removed from the activity
    """
    subject = pgettext('platform-email', 'You have withdrawn from the activity "{title}"')
    template = 'messages/participants/user_date_participant_withdrew'

    def get_context(self, recipient):
        context = super(UserDateParticipantWithdrewNotification, self).get_context(recipient)
        if self.obj.slot and self.obj.slot.start:
            context['slot'] = get_slot_info(self.obj.slot)
        return context


class UserScheduledNotification(UserParticipantNotification):
    """
    The participant was removed from the activity
    """
    subject = pgettext('platform-email', 'You have been scheduled for the activity "{title}"')
    template = 'messages/participants/user_participant_scheduled'

    def get_context(self, recipient):
        context = super(UserScheduledNotification, self).get_context(recipient)
        if self.obj.slot and self.obj.slot.start:
            context['slot'] = get_slot_info(self.obj.slot)
        return context


class RegisteredActivityParticipantAddedNotification(TransitionMessage):
    """
    A participant was added
    """
    subject = pgettext('platform-email', 'You have been added to the activity "{title}"')
    template = 'messages/participants/registered_date_participant_added'
    context = {
        'title': 'activity.title',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('platform-email', 'View activity')

    def get_recipients(self):
        """participant"""
        if self.obj.user:
            return [self.obj.user]
        else:
            return []
