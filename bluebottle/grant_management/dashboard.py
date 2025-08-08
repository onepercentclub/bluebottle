from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.grant_management.models import GrantPayout


class GrantPayoutsReadForApprovalDashboardModule(DashboardModule):
    title = _('Grant payouts ready for approval')
    title_url = "{}?status=new".format(reverse('admin:grant_management_grantpayout_changelist'))
    template = 'dashboard/payouts_ready_for_approval.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        payouts = GrantPayout.objects.filter(status='new').order_by('created')
        user = context.request.user
        if user.segment_manager.count():
            return payouts.filter(
                Q(activity__segments__in=user.segment_manager.all())
            ).distinct()

        self.children = payouts[:self.limit]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(GrantPayoutsReadForApprovalDashboardModule())
