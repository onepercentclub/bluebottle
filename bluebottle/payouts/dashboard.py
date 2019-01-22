from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _

from jet.dashboard.modules import DashboardModule

from bluebottle.payouts.models import StripePayoutAccount


class PayoutAccountsNeedingAction(DashboardModule):
    title = _('Payout accounts that need action')
    title_url = "{}?reviewed__exact=0".format(
        reverse('admin:payouts_payoutaccount_changelist')
    )
    template = 'dashboard/payout_accounts_needing_actions.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        payout_accounts = StripePayoutAccount.objects.filter(
            reviewed=False, project__status__slug='plan-submitted'
        ).order_by('-created')
        self.children = payout_accounts[:self.limit]
