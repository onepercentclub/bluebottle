from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings


class RecentInitiatives(DashboardModule):
    title = _('Recently submitted initiatives')
    title_url = "{}?status__exact=submitted".format(reverse('admin:initiatives_initiative_changelist'))
    template = 'dashboard/recent_initiatives.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        initiatives = Initiative.objects.filter(status='submitted').order_by('-created')
        self.children = initiatives[:self.limit]


class MyOfficeInitiatives(DashboardModule):
    title = _("Recently submitted initiatives for my office: {location}")
    title_url = "{}".format(reverse('admin:initiatives_initiative_changelist'))
    template = 'dashboard/recent_initiatives.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        location = context.request.user.location
        self.children = Initiative.objects.filter(location=location).order_by('-created')[:self.limit]

    def load_from_model(self):
        super(MyOfficeInitiatives, self).load_from_model()
        if hasattr(self.context, 'request'):
            location = self.context.request.user.location
            self.title = self.title.format(location=location)
            self.title_url += "?location__id__exact={}".format(location.id)


class MyOfficeSubRegionInitiatives(DashboardModule):
    title = _("Recently submitted initiatives for my office group: {location}")
    title_url = "{}".format(reverse('admin:initiatives_initiative_changelist'))
    template = 'dashboard/recent_initiatives.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        location = context.request.user.location
        self.children = Initiative.objects.filter(
            location__subregion=location.subregion
        ).order_by('-created')[:self.limit]

    def load_from_model(self):
        super(MyOfficeSubRegionInitiatives, self).load_from_model()
        if hasattr(self.context, 'request'):
            location = self.context.request.user.location
            self.title = self.title.format(location=location.subregion)
            self.title_url += "?location__subregion__id__exact={}".format(location.subregion.id)


class MyOfficeRegionInitiatives(DashboardModule):
    title = _("Recently submitted initiatives for my office region: {location}")
    title_url = "{}".format(reverse('admin:initiatives_initiative_changelist'))
    template = 'dashboard/recent_initiatives.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        location = context.request.user.location
        self.children = Initiative.objects.filter(
            location__subregion__region=location.subregion.region
        ).order_by('-created')[:self.limit]

    def load_from_model(self):
        super(MyOfficeRegionInitiatives, self).load_from_model()
        if hasattr(self.context, 'request'):
            location = self.context.request.user.location
            self.title = self.title.format(location=location.subregion.region)
            self.title_url += "?location__subregion__region__id__exact={}".format(location.subregion.region.id)


class MyReviewingInitiatives(DashboardModule):
    title = _("Initiatives I'm reviewing")
    title_url = "{}?reviewer=True".format(reverse('admin:initiatives_initiative_changelist'))
    template = 'dashboard/recent_initiatives.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        user = context.request.user
        self.children = Initiative.objects.filter(reviewer=user).order_by('-created')[:self.limit]


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.children.append(RecentInitiatives())
        self.children.append(MyReviewingInitiatives())
        user = context.request.user
        if user.location:
            self.children.append(MyOfficeInitiatives())
            if InitiativePlatformSettings.objects.get().enable_office_regions:
                self.children.append(MyOfficeSubRegionInitiatives())
                self.children.append(MyOfficeRegionInitiatives())
