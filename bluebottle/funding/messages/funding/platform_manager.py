from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.activities.messages.reviewer import get_reviewers_for_activity
from bluebottle.funding.models import Funding
from bluebottle.grant_management.models import GrantApplication
from bluebottle.notifications.messages import TransitionMessage


class LivePayoutAccountMarkedIncomplete(TransitionMessage):
    """
    A payout account that is connected to a live crowdfunding campaign was marked incomplete
    """
    subject = pgettext('platform-email',
                       u'Failed identity verification for a running crowdfunding campaign on {site_name} ⚠️')
    template = 'messages/platform_manager/live_payout_account_rejected'

    context = {
        'id': 'id'
    }

    def get_recipients(self):
        """platform support email addresses"""
        recipients = []

        campaigns = Funding.objects.filter(
            bank_account__connect_account=self.obj,
            status__in=['open', 'on_hold']
        ).all()

        for campaign in campaigns:
            recipients = recipients + get_reviewers_for_activity(campaign)

        applications = GrantApplication.objects.filter(
            bank_account__connect_account=self.obj,
            status__in=['granted']
        )

        for application in applications:
            recipients = recipients + get_reviewers_for_activity(application)

        return list(set(recipients))


class LivePublicPayoutAccountMarkedIncomplete(LivePayoutAccountMarkedIncomplete):
    """
    A public payout account that is connected to a live crowdfunding campaign was marked incomplete
    """
    subject = pgettext('platform-email',
                       u'Incomplete payout account for a running crowdfunding campaign on {site_name} ⚠️')
    template = 'messages/platform_manager/live_public_payout_account_rejected'
