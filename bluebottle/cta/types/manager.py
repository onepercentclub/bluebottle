from datetime import timedelta

from django.utils import timezone
from django.utils.translation import gettext as _
from elasticsearch_dsl import Q as ESQ

from bluebottle.cta.framework import ActionItem, ActionType, registry
from bluebottle.cta.types.base import activity_search, activity_url, managed_by

LIVE_STATUSES = ['open', 'full', 'registration_closed', 'running']


@registry.register
class PendingRegistrations(ActionType):
    slug = 'pending_registrations'
    audience = 'manager'
    group = 'decision'
    priority = 10

    def get_items(self, user):
        search = activity_search(
            managed_by(user),
            ESQ('terms', status=LIVE_STATUSES),
            ESQ('range', **{'registration_stats.pending': {'gt': 0}}),
        )
        for hit in search:
            count = hit.registration_stats.pending
            yield ActionItem(
                type=self.slug,
                object_id=int(hit.meta.id),
                group=self.group,
                severity='urgent',
                title=hit.title,
                message=_('%(count)d people are waiting for you to accept or reject their registration.') % {
                    'count': count
                },
                count=count,
                url=activity_url(hit),
                created=getattr(hit, 'created', None),
            )


@registry.register
class WaitingList(ActionType):
    slug = 'waiting_list'
    audience = 'manager'
    group = 'decision'
    priority = 20

    def get_items(self, user):
        search = activity_search(
            managed_by(user),
            ESQ('term', status='full'),
            ESQ('range', **{'contributor_stats.interested': {'gt': 0}}),
        )
        for hit in search:
            count = hit.contributor_stats.interested
            yield ActionItem(
                type=self.slug,
                object_id=int(hit.meta.id),
                group=self.group,
                severity='attention',
                title=hit.title,
                message=_('This activity is full and %(count)d people are on the waiting list. '
                          'Consider raising the capacity.') % {'count': count},
                count=count,
                url=activity_url(hit),
                created=getattr(hit, 'created', None),
            )


@registry.register
class NotFullUpcoming(ActionType):
    slug = 'not_full_upcoming'
    audience = 'manager'
    group = 'participation'
    priority = 30
    days = 14
    threshold = 0.5

    def get_items(self, user):
        now = timezone.now()
        search = activity_search(
            managed_by(user),
            ESQ('term', status='open'),
            ESQ('exists', field='capacity'),
            ESQ('range', start={'gte': now, 'lte': now + timedelta(days=self.days)}),
        )
        for hit in search:
            capacity = hit.capacity
            if not capacity:
                continue
            filled = hit.contributor_count or 0
            if filled / capacity >= self.threshold:
                continue
            yield ActionItem(
                type=self.slug,
                object_id=int(hit.meta.id),
                group=self.group,
                severity='info',
                title=hit.title,
                message=_('Starting soon and only %(filled)d of %(capacity)d spots are filled. '
                          'Share it to find more participants.') % {
                    'filled': filled, 'capacity': capacity
                },
                count=capacity - filled,
                url=activity_url(hit),
                created=getattr(hit, 'created', None),
            )


@registry.register
class NeedsWork(ActionType):
    slug = 'needs_work'
    audience = 'manager'
    group = 'decision'
    priority = 15

    def get_items(self, user):
        search = activity_search(managed_by(user), ESQ('term', status='needs_work'))
        for hit in search:
            yield ActionItem(
                type=self.slug,
                object_id=int(hit.meta.id),
                group=self.group,
                severity='attention',
                title=hit.title,
                message=_('The reviewer asked for changes. Update your activity and submit it again.'),
                url=activity_url(hit),
                created=getattr(hit, 'created', None),
            )


@registry.register
class StaleDraft(ActionType):
    slug = 'draft_stale'
    audience = 'manager'
    group = 'decision'
    priority = 40
    days = 7

    def get_items(self, user):
        cutoff = timezone.now() - timedelta(days=self.days)
        search = activity_search(
            managed_by(user),
            ESQ('term', status='draft'),
            ESQ('range', created={'lte': cutoff}),
        )
        for hit in search:
            yield ActionItem(
                type=self.slug,
                object_id=int(hit.meta.id),
                group=self.group,
                severity='info',
                title=hit.title,
                message=_('This draft has been waiting for more than %(days)d days. '
                          'Finish it and submit it for review.') % {'days': self.days},
                url=activity_url(hit),
                created=getattr(hit, 'created', None),
            )
