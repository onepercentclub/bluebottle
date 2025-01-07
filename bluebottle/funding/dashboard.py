from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.funding.models import Funding, Payout, PaymentProvider
from bluebottle.offices.admin import region_manager_filter


class RecentFunding(DashboardModule):
    title = _('Recently submitted funding activities')
    title_url = "{}?status[]=submitted".format(reverse('admin:funding_funding_changelist'))
    template = 'dashboard/recent_funding.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        activities = Funding.objects.filter(status='submitted').order_by('-created')
        user = context.request.user
        activities = region_manager_filter(activities, user)
        self.children = activities[:self.limit]


class PayoutsReadForApprovalDashboardModule(DashboardModule):
    title = _('Payouts ready for approval')
    title_url = "{}?status[]=draft&status[]=new".format(reverse('admin:funding_payout_changelist'))
    template = 'dashboard/payouts_ready_for_approval.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        payouts = Payout.objects.filter(status='new').order_by('created')
        user = context.request.user
        payouts = region_manager_filter(payouts, user)
        self.children = payouts[:self.limit]


class BankaccountsDashboardModule(DashboardModule):
    title = _('Bank account lists')
    template = 'dashboard/bank_account_lists.html'

    def init_with_context(self, context):
        self.children = [
            {
                'name': '{} {}'.format(provider.name.title(), _('Bank Accounts')),
                'url':
                    'admin:funding_stripe_externalaccount_changelist'
                    if provider.name == 'stripe'
                    else 'admin:funding_{0}_{0}bankaccount_changelist'.format(provider.name.lower())
            }
            for provider in PaymentProvider.objects.all()
        ]


class PaymentDashboardModule(DashboardModule):
    title = _('Payment lists')
    template = 'dashboard/payment_lists.html'

    def init_with_context(self, context):
        self.children = [
            {
                'name': '{} {}'.format(provider.name.title(), _('Payments')),
                'url':
                    'admin:funding_stripe_stripepayment_changelist'
                    if provider.name == 'stripe'
                    else 'admin:funding_{0}_{0}payment_changelist'.format(provider.name.lower())
            }
            for provider in PaymentProvider.objects.all()
        ]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(RecentFunding())
        self.children.append(PayoutsReadForApprovalDashboardModule())
        self.children.append(BankaccountsDashboardModule())
        self.children.append(PaymentDashboardModule())
