# -*- coding: utf-8 -*-

from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.funding_stripe.models import StripePayoutAccount
from bluebottle.notifications.messages import TransitionMessage


class GrantApplicationManagerMessage(TransitionMessage):
    context = {
        'title': 'title',
    }

    action_title = pgettext('email', 'View application')

    def get_context(self, recipient):
        if isinstance(self.obj, StripePayoutAccount):
            self.obj = self.obj.funding.first() or self.obj.grant_application.first()

        context = super(GrantApplicationManagerMessage, self).get_context(recipient)
        # Safely access organization attribute
        organization = getattr(self.obj, 'organization', None)
        context['partner_organization'] = organization and getattr(organization, 'name', None)
        return context

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]

    class Meta:
        abstract = True


class GrantApplicationRejectedMessage(GrantApplicationManagerMessage):
    subject = pgettext('email', "Your grant application on {site_name} has been rejected")
    template = 'messages/grant_application/activity_manager/application_rejected'


class GrantApplicationSubmittedMessage(GrantApplicationManagerMessage):
    subject = pgettext('email', "You have submitted a grant application on {site_name}")
    template = 'messages/grant_application/activity_manager/application_submitted'


class GrantApplicationNeedsWorkMessage(GrantApplicationManagerMessage):
    subject = pgettext('email', u"The grant application you submitted on {site_name} needs work")
    template = 'messages/grant_application/activity_manager/application_needs_work'


class GrantApplicationApprovedMessage(GrantApplicationManagerMessage):
    subject = pgettext('email', 'Your grant application on {site_name} has been approved!')
    template = 'messages/grant_application/activity_manager/application_approved'


class GrantApplicationCancelledMessage(GrantApplicationManagerMessage):
    subject = pgettext('email', u'Your grant application on {site_name} has been cancelled')
    template = 'messages/grant_application/activity_manager/application_cancelled'


class GrantApplicationPayoutAccountRejected(GrantApplicationManagerMessage):
    subject = pgettext('email', u'Action required for your grant application')
    template = 'messages/grant_application/activity_manager/payout_account_rejected'

    @property
    def action_link(self):
        return self.obj.grant_application.get_absolute_url()


class GrantApplicationPayoutAccountMarkedIncomplete(GrantApplicationManagerMessage):
    subject = pgettext('email', "Action required for your grant application")
    template = "messages/grant_application/activity_manager/payout_account_marked_incomplete"

    @property
    def action_link(self):
        return self.obj.grant_application.get_absolute_url()


class GrantApplicationPayoutAccountVerified(GrantApplicationManagerMessage):
    subject = pgettext('email', u'Your identity has been verified')
    template = 'messages/grant_application/activity_manager/payout_account_verified'

    @property
    def action_link(self):
        return self.obj.grant_application.get_absolute_url()
