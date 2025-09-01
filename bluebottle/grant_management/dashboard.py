from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.grant_management.models import GrantPayout, GrantApplication
from bluebottle.segments.filters import segment_filter


class GrantPayoutsReadyForApprovalDashboardModule(DashboardModule):
    title = _('Grant payouts ready for approval')
    title_url = "{}?status=new".format(reverse('admin:grant_management_grantpayout_changelist'))
    template = 'dashboard/grant_payouts_ready_for_approval.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        payouts = GrantPayout.objects.filter(status='new').order_by('created')
        user = context.request.user
        if user.segment_manager.count():
            payouts = segment_filter(payouts, user)
        self.children = payouts[:self.limit]


class GrantApplicationsReadyForApprovalDashboardModule(DashboardModule):
    title = _('Grant applications to be reviewed')
    title_url = "{}?status=new".format(reverse('admin:grant_management_grantapplication_changelist'))
    template = 'dashboard/grant_applications_ready_for_review.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        applications = GrantApplication.objects.filter(status='submitted').order_by('created')
        user = context.request.user
        if user.segment_manager.count():
            applications = segment_filter(applications, user)
        self.children = applications[:self.limit]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(GrantApplicationsReadyForApprovalDashboardModule())
        self.children.append(GrantPayoutsReadyForApprovalDashboardModule())
