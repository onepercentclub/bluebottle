from django_tools.middlewares.ThreadLocal import get_current_user
from elasticsearch_dsl.faceted_search import TermsFacet
from elasticsearch_dsl.query import Term

from bluebottle.initiatives.documents import initiative
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.segments.models import SegmentType
from bluebottle.utils.filters import (
    ElasticSearchFilter, Search, TranslatedFacet, NamedNestedFacet,
    SegmentFacet
)


class OwnerFacet(TermsFacet):
    def __init__(self, **kwargs):
        super().__init__(field='owner', **kwargs)

    def add_filter(self, filter_values):
        if filter_values:
            user = get_current_user()
            if user.is_authenticated:
                return Term(owner=user.pk)


class InitiativeSearch(Search):
    doc_types = [initiative]

    sorting = {
        'date_created': ['-created'],
        'open_activities': ['-open_activities_count', '-succeeded_activities_count'],
    }

    fields = [
        (None, ('title^3', 'story^2', 'pitch')),
    ]

    facets = {
        'owner': OwnerFacet(),
    }

    possible_facets = {
        'theme': TranslatedFacet('theme'),
        'category': TranslatedFacet('categories', 'title'),
        'country': NamedNestedFacet('country'),
        'location': NamedNestedFacet('office'),
    }

    def __new__(cls, *args, **kwargs):
        settings = InitiativePlatformSettings.objects.get()
        result = super().__new__(cls, settings.activity_search_filters)

        for segment_type in SegmentType.objects.all():
            result.facets[f'segment.{segment_type.slug}'] = SegmentFacet(segment_type)

        return result

    def query(self, search, query):
        search = super().query(search, query)
        if 'owner' not in self._filters:
            search = search.filter(Term(status='approved'))
        return search


class InitiativeSearchFilter(ElasticSearchFilter):
    index = initiative
    search_class = InitiativeSearch
