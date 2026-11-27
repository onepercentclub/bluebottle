from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class OrganizationMemberMessage(TransitionMessage):
    """
    Message about a membership change. The object is the organisation,
    the recipient is passed as the `member` option, so the message can
    also be sent for a membership that no longer exists.
    """
    context = {'organization_name': 'name'}

    def get_recipients(self):
        return [self.options['member']]


class OrganizationMemberAddedMessage(OrganizationMemberMessage):
    subject = pgettext('platform-email', "You've been added to {organization_name}")
    template = 'messages/organization_member_added'
    action_title = pgettext('platform-email', 'View organisation')

    @property
    def action_link(self):
        return self.obj.get_absolute_url()


class OrganizationMemberRemovedMessage(OrganizationMemberMessage):
    subject = pgettext('platform-email', "You've been removed from {organization_name}")
    template = 'messages/organization_member_removed'
