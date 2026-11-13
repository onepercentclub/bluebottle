from django.conf import settings
from elasticsearch_dsl import Q as ESQ

from bluebottle.activities.documents import activity
from bluebottle.clients.utils import tenant_url

DETAIL_PATHS = {
    'dateactivity': 'date',
    'deadlineactivity': 'deadline',
    'periodicactivity': 'periodic',
    'scheduleactivity': 'schedule',
    'registereddateactivity': 'registered-date',
    'deed': 'deed',
    'funding': 'funding',
    'collectactivity': 'collect',
    'grantapplication': 'grant-application',
}

SOURCE_FIELDS = [
    'title', 'slug', 'status', 'type', 'created', 'start', 'end', 'capacity',
    'contributor_count', 'contributor_stats', 'registration_stats',
]


def activity_search(*filters, limit=50):
    search = activity.search().source(SOURCE_FIELDS)
    for query in filters:
        search = search.filter(query)
    return search[:limit]


def managed_by(user):
    return ESQ('term', manager=user.pk)


def activity_url(hit):
    segment = DETAIL_PATHS.get(hit.type, hit.type)
    return '/activities/details/{}/{}/{}'.format(segment, hit.meta.id, hit.slug)


def manage_url(hit):
    return activity_url(hit)


def demo_enabled():
    return getattr(settings, 'CTA_DEMO_ACTIONS', False)


__all__ = ['activity_search', 'managed_by', 'activity_url', 'demo_enabled', 'tenant_url']
