import importlib

from django.utils.translation import gettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import Dashboard, DefaultAppIndexDashboard

from bluebottle.activities.dashboard import RecentActivities, RecentContributors, UnPublishedActivities
from bluebottle.funding.dashboard import RecentFunding, PayoutsReadForApprovalDashboardModule
from bluebottle.initiatives.dashboard import MyReviewingInitiatives, RecentInitiatives
from bluebottle.members.dashboard import RecentMembersDashboard
from bluebottle.updates.dashboard import RecentUpdates


class CustomIndexDashboard(Dashboard):
    columns = 2

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)

        # Initiatives
        self.children.append(MyReviewingInitiatives())
        self.children.append(RecentInitiatives())
        self.children.append(UnPublishedActivities())

        # Activities
        self.children.append(RecentActivities())
        self.children.append(RecentFunding())
        self.children.append(RecentContributors())

        # Wallposts
        self.children.append(RecentUpdates())

        # Payouts
        self.children.append(PayoutsReadForApprovalDashboardModule())

        # Other
        self.children.append(modules.RecentActions(
            _('Recent Actions'),
            10,
            column=0,
            order=0
        ))
        self.children.append(RecentMembersDashboard())


class CustomAppIndexDashboard(DefaultAppIndexDashboard):

    def __new__(cls, context, **kwargs):
        try:
            mod = importlib.import_module("bluebottle.{}.dashboard".format(kwargs['app_label']))
            dash = mod.AppIndexDashboard(context, **kwargs)
            return dash
        except ImportError:
            return DefaultAppIndexDashboard(context, **kwargs)
