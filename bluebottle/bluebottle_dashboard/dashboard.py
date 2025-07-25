import importlib

from django.utils.translation import gettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import Dashboard, DefaultAppIndexDashboard

from bluebottle.activities.dashboard import (
    RecentlySubmittedActivities,
    RecentlyPublishedActivities,
    RecentContributors,
    UnPublishedActivities
)
from bluebottle.funding.dashboard import RecentFunding, PayoutsReadForApprovalDashboardModule
from bluebottle.grant_management.dashboard import GrantPayoutsReadForApprovalDashboardModule
from bluebottle.initiatives.dashboard import (
    MyReviewingInitiatives, RecentlyPublishedInitiatives, RecentlySubmittedInitiatives
)
from bluebottle.members.dashboard import RecentMembersDashboard
from bluebottle.updates.dashboard import RecentUpdates


class CustomIndexDashboard(Dashboard):
    columns = 2

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)

        # Initiatives
        self.children.append(MyReviewingInitiatives())
        self.children.append(RecentlySubmittedInitiatives())
        self.children.append(RecentlyPublishedInitiatives())
        self.children.append(UnPublishedActivities())

        # Activities
        self.children.append(RecentlySubmittedActivities())
        self.children.append(RecentlyPublishedActivities())
        self.children.append(RecentFunding())
        self.children.append(RecentContributors())

        # Wallposts
        self.children.append(RecentUpdates())

        # Payouts
        self.children.append(PayoutsReadForApprovalDashboardModule())
        self.children.append(GrantPayoutsReadForApprovalDashboardModule())

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
