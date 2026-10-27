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
from bluebottle.funding.dashboard import RecentFunding, PayoutsReadyForApprovalDashboardModule
from bluebottle.grant_management.dashboard import GrantPayoutsReadyForApprovalDashboardModule, \
    GrantApplicationsReadyForApprovalDashboardModule
from bluebottle.initiatives.dashboard import (
    MyReviewingInitiatives, RecentlyPublishedInitiatives, RecentlySubmittedInitiatives
)
from bluebottle.members.dashboard import RecentMembersDashboard
from bluebottle.updates.dashboard import RecentUpdates


def can_view(user, app_label, model_name):
    return (
        user.has_perm('{}.view_{}'.format(app_label, model_name)) or
        user.has_perm('{}.change_{}'.format(app_label, model_name))
    )


MODULE_PERMISSIONS = [
    (MyReviewingInitiatives, ('initiatives', 'initiative')),
    (RecentlySubmittedInitiatives, ('initiatives', 'initiative')),
    (RecentlyPublishedInitiatives, ('initiatives', 'initiative')),
    (UnPublishedActivities, ('activities', 'activity')),
    (RecentlySubmittedActivities, ('activities', 'activity')),
    (RecentlyPublishedActivities, ('activities', 'activity')),
    (RecentFunding, ('funding', 'funding')),
    (RecentContributors, ('activities', 'contributor')),
    (GrantApplicationsReadyForApprovalDashboardModule, ('grant_management', 'grantapplication')),
    (RecentUpdates, ('updates', 'update')),
    (PayoutsReadyForApprovalDashboardModule, ('funding', 'payout')),
    (GrantPayoutsReadyForApprovalDashboardModule, ('grant_management', 'grantpayout')),
    (RecentMembersDashboard, ('members', 'member')),
]


def can_view_module(user, module):
    for module_class, (app_label, model_name) in MODULE_PERMISSIONS:
        if isinstance(module, module_class):
            return can_view(user, app_label, model_name)
    return True


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
        self.children.append(GrantApplicationsReadyForApprovalDashboardModule())

        # Updates
        self.children.append(RecentUpdates())

        # Payouts
        self.children.append(PayoutsReadyForApprovalDashboardModule())
        self.children.append(GrantPayoutsReadyForApprovalDashboardModule())

        # Other
        self.children.append(modules.RecentActions(
            _('Recent Actions'),
            10,
            column=0,
            order=0
        ))
        self.children.append(RecentMembersDashboard())

        user = context['request'].user
        self.children = [module for module in self.children if can_view_module(user, module)]

    def load_modules(self):
        # Layouts are stored per user, so modules saved before a permission change still have to be filtered.
        super().load_modules()
        user = self.context['request'].user
        self.modules = [module for module in self.modules if can_view_module(user, module)]


class CustomAppIndexDashboard(DefaultAppIndexDashboard):

    def __new__(cls, context, **kwargs):
        try:
            mod = importlib.import_module("bluebottle.{}.dashboard".format(kwargs['app_label']))
            dash = mod.AppIndexDashboard(context, **kwargs)
            return dash
        except ImportError:
            return DefaultAppIndexDashboard(context, **kwargs)
