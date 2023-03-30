from bluebottle.initiatives.models import InitiativePlatformSettings

from elasticsearch_dsl import (
    TermsFacet
)

from bluebottle.activities.documents import Activity, activity
from bluebottle.segments.models import SegmentType
from bluebottle.utils.filters import (
    ElasticSearchFilter, Search, TranslatedFacet, DateRangeFacet, NamedNestedFacet,
    SegmentFacet
)


class ActivitySearch(Search):

    doc_types = [Activity]
    fields = [
        (None, ('title^3', 'description^2')),
        ('initiative', ('title^2', 'story', 'pitch')),
        ('slots', ('title',)),
    ]

    facets = {
        'upcoming': TermsFacet(field='is_upcoming'),
        'activity-type': TermsFacet(field='activity_type'),
        'highlight': TermsFacet(field='highlight'),
    }

    possible_facets = {
        'team_activity': TermsFacet(field='team_activity'),
        'theme': TranslatedFacet('theme'),
        'category': TranslatedFacet('categories', 'title'),
        'skill': TranslatedFacet('expertise'),
        'country': NamedNestedFacet('country'),
        'location': NamedNestedFacet('office'),
        'date': DateRangeFacet(field='duration', calendar_interval="day"),
    }

    def __new__(cls, search, filter):
        settings = InitiativePlatformSettings.objects.get()
        result = super().__new__(cls, settings.activity_search_filters)

        for segment_type in SegmentType.objects.all():
            result.facets[f'segment.{segment_type.slug}'] = SegmentFacet(segment_type)

        return result


class ActivitySearchFilter(ElasticSearchFilter):
    index = activity
    search_class = ActivitySearch
