# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext

from bluebottle.notifications.messages import TransitionMessage


class GrantApplicationManagerMessage(TransitionMessage):
    context = {
        'title': 'title',
    }

    action_title = pgettext('email', 'View application')

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    def get_recipients(self):
        """the activity organizer"""
        return [self.obj.owner]


class GrantApplicationRejectedMessage(GrantApplicationManagerMessage):
    subject = _("Your grant application on {site_name} has been rejected")
    template = 'messages/funding/grant_application/activity_manager/application_rejected'


class GrantApplicationSubmittedMessage(GrantApplicationManagerMessage):
    subject = _("You have submitted a grant application on {site_name}")
    template = 'messages/funding/grant_application/activity_manager/application_submitted'


class GrantApplicationNeedsWorkMessage(GrantApplicationManagerMessage):
    subject = _(u"The grant application you submitted on {site_name} needs work")
    template = 'messages/funding/grant_application/activity_manager/application_needs_work'


class GrantApplicationApprovedMessage(GrantApplicationManagerMessage):
    subject = _('Your grant application on {site_name} has been approved!')
    template = 'messages/funding/grant_application/activity_manager/application_approved'


class GrantApplicationCancelledMessage(GrantApplicationManagerMessage):
    subject = _(u'Your grant application on {site_name} has been cancelled')
    template = 'messages/funding/grant_application/activity_manager/application_cancelled'


class PayoutAccountRejected(GrantApplicationManagerMessage):
    subject = _(u'Action required for your grant application')
    template = 'messages/funding/grant_application/activity_manager/payout_account_rejected'


class PayoutAccountMarkedIncomplete(GrantApplicationManagerMessage):
    subject = _("Action required for your grant application")
    template = "messages/funding/grant_application/activity_manager/payout_account_marked_incomplete"


class PayoutAccountVerified(GrantApplicationManagerMessage):
    subject = _(u'Your identity has been verified')
    template = 'messages/funding/grant_application/activity_manager/payout_account_verified'
