from django.db.models import Q
from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.activity_pub.models import Event
from bluebottle.activity_pub.utils import activity_pub_verbose_type, safe_get_real_instance
from bluebottle.cms.models import SitePlatformSettings


def prepare_events(events):
    for event in events:
        real_instance = safe_get_real_instance(event)
        if real_instance:
            model_name = real_instance._meta.model_name
            app_label = real_instance._meta.app_label
            event.admin_url = reverse(
                f'admin:{app_label}_{model_name}_change',
                args=[event.pk],
            )
            event.type_label = real_instance._meta.verbose_name
        else:
            event.admin_url = reverse(
                'admin:activity_pub_event_change',
                args=[event.pk],
            )
            event.type_label = activity_pub_verbose_type(event)
    return events


class RecentlyReceivedActivities(DashboardModule):
    title = _('Recently received activities')
    title_url = reverse('admin:activity_pub_receivedactivity_changelist')
    template = 'dashboard/recent_events.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        events = Event.objects.filter(
            iri__isnull=False,
        ).order_by('-id')[:self.limit]
        self.children = prepare_events(events)


class RecentlyAdoptedActivities(DashboardModule):
    title = _('Recently adopted activities')
    title_url = '{}?adopted=yes'.format(
        reverse('admin:activity_pub_receivedactivity_changelist')
    )
    template = 'dashboard/recent_events.html'
    limit = 5
    column = 0

    def init_with_context(self, context):
        events = Event.objects.filter(
            iri__isnull=False,
        ).filter(
            Q(adopted__isnull=False) | Q(link__isnull=False)
        ).order_by('-id')[:self.limit]
        self.children = prepare_events(events)


class PendingAdoptionActivities(DashboardModule):
    title = _('Received activities awaiting adoption')
    title_url = '{}?adopted=no'.format(
        reverse('admin:activity_pub_receivedactivity_changelist')
    )
    template = 'dashboard/recent_events.html'
    limit = 5
    column = 1

    def init_with_context(self, context):
        events = Event.objects.filter(
            iri__isnull=False,
            adopted__isnull=True,
            link__isnull=True,
        ).order_by('-id')[:self.limit]
        self.children = prepare_events(events)


class RecentlyPublishedActivities(DashboardModule):
    title = _('Recently shared activities')
    title_url = reverse('admin:activity_pub_publishedactivity_changelist')
    template = 'dashboard/recent_events.html'
    limit = 5
    column = 1

    def init_with_context(self, context):
        events = Event.objects.filter(
            iri__isnull=True,
        ).order_by('-id')[:self.limit]
        self.children = prepare_events(events)


class ActivityPubQuickLinks(DashboardModule):
    title = _('GoodUp Connect')
    template = 'dashboard/quick_links.html'
    column = 0

    def init_with_context(self, context):
        settings = SitePlatformSettings.load()
        links = []

        if settings.is_receiving_activities:
            links.extend([
                {
                    'name': _('Received activities'),
                    'url': 'admin:activity_pub_receivedactivity_changelist',
                },
                {
                    'name': _('Connected suppliers'),
                    'url': 'admin:activity_pub_following_changelist',
                },
            ])

        if settings.is_publishing_activities:
            links.extend([
                {
                    'name': _('Shared activities'),
                    'url': 'admin:activity_pub_publishedactivity_changelist',
                },
                {
                    'name': _('Connected consumers'),
                    'url': 'admin:activity_pub_follower_changelist',
                },
            ])

        self.children = links


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)

        settings = SitePlatformSettings.load()

        if settings.is_sharing_activities:
            self.children.append(ActivityPubQuickLinks())

        if settings.is_receiving_activities:
            self.children.append(PendingAdoptionActivities())
            self.children.append(RecentlyReceivedActivities())
            self.children.append(RecentlyAdoptedActivities())

        if settings.is_publishing_activities:
            self.children.append(RecentlyPublishedActivities())
