from django.db.models import Q
from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from jet.dashboard.modules import DashboardModule

from bluebottle.activity_pub.models import Accept, Event, Follower, Following
from bluebottle.activity_pub.utils import get_platform_actor
from bluebottle.cms.models import SitePlatformSettings


def prepare_events(events):
    for event in events:
        real_instance = event.get_real_instance()
        model_name = real_instance._meta.model_name
        app_label = real_instance._meta.app_label
        event.admin_url = reverse(
            f'admin:{app_label}_{model_name}_change',
            args=[event.pk],
        )
        event.type_label = real_instance._meta.verbose_name
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


def get_accepted_follow_ids(follows):
    return set(
        Accept.objects.filter(
            object_id__in=follows.values_list('pk', flat=True)
        ).values_list('object_id', flat=True)
    )


def prepare_connections(follows, name_attr, change_url_name, accepted_ids):
    connections = []
    for follow in follows:
        accepted = follow.pk in accepted_ids
        connections.append({
            'name': str(getattr(follow, name_attr)),
            'admin_url': reverse(change_url_name, args=[follow.pk]),
            'accepted': accepted,
            'status': _('Accepted') if accepted else _('Requested'),
            'shared_activities': follow.shared_activities.count(),
        })
    return connections


class ActivityPubConnections(DashboardModule):
    title = _('Connected platforms')
    template = 'dashboard/connections.html'
    column = 0
    limit = 10

    def init_with_context(self, context):
        settings = SitePlatformSettings.load()
        platform_actor = get_platform_actor()
        self.show_suppliers = settings.is_receiving_activities
        self.show_consumers = settings.is_publishing_activities
        self.suppliers = []
        self.consumers = []

        if not platform_actor:
            self.children = []
            return

        if self.show_suppliers:
            suppliers = Following.objects.filter(
                actor=platform_actor
            ).select_related('object').order_by('-id')[:self.limit]
            accepted_ids = get_accepted_follow_ids(suppliers)
            self.suppliers = prepare_connections(
                suppliers,
                'object',
                'admin:activity_pub_following_change',
                accepted_ids,
            )

        if self.show_consumers:
            consumers = Follower.objects.filter(
                object=platform_actor
            ).select_related('actor').order_by('-id')[:self.limit]
            accepted_ids = get_accepted_follow_ids(consumers)
            self.consumers = prepare_connections(
                consumers,
                'actor',
                'admin:activity_pub_follower_change',
                accepted_ids,
            )

        self.children = self.suppliers + self.consumers


class AppIndexDashboard(DefaultAppIndexDashboard):

    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)

        settings = SitePlatformSettings.load()

        if settings.is_sharing_activities:
            self.children.append(ActivityPubQuickLinks())
            self.children.append(ActivityPubConnections())

        if settings.is_receiving_activities:
            self.children.append(PendingAdoptionActivities())
            self.children.append(RecentlyReceivedActivities())
            self.children.append(RecentlyAdoptedActivities())

        if settings.is_publishing_activities:
            self.children.append(RecentlyPublishedActivities())
