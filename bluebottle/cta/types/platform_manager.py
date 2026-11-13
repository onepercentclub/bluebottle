from django.utils.translation import gettext as _
from elasticsearch_dsl import Q as ESQ

from bluebottle.activities.filters import reviewer_filter
from bluebottle.cta.framework import ActionItem, ActionType, registry
from bluebottle.cta.types.base import activity_search


@registry.register
class ReviewSubmitted(ActionType):
    slug = 'review_submitted'
    audience = 'platform_manager'
    group = 'decision'
    priority = 5

    def get_items(self, user):
        search = activity_search(
            ESQ('term', status='submitted'),
            reviewer_filter(user),
            limit=0,
        )
        count = search.count()
        if not count:
            return

        yield ActionItem(
            type=self.slug,
            object_id=0,
            group=self.group,
            severity='urgent',
            title=_('Activities to review'),
            message=_('%(count)d submitted activities are waiting for your review.') % {'count': count},
            count=count,
            url='/activities/review',
        )
