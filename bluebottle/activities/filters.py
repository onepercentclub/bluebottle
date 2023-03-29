import re
from bluebottle.initiatives.models import InitiativePlatformSettings

from bluebottle.utils.utils import get_current_language
from elasticsearch_dsl.query import (
    Terms, Term, Nested,
)

from elasticsearch_dsl import (
    FacetedSearch, TermsFacet, Facet
)

from elasticsearch_dsl.aggs import Bucket, A

from bluebottle.activities.documents import activity, Activity
from bluebottle.segments.models import SegmentType
from bluebottle.utils.filters import ElasticSearchFilter


class MultiTerms(Bucket):  # noqa
    name = "multi_terms"


class MultiTermsFacet(Facet):
    agg_type = 'multi_terms'

    def add_filter(self, filter_values):
        if filter_values:
            return Terms(
                _expand__to_dot=False, **{self._params["terms"][-1]['field']: filter_values}
            )

    def is_filtered(self, key, filter_values):
        """
        Is a filter active on the given key.
        """
        return key[-1] in filter_values


class NamedNestedFacet(Facet):
    def __init__(self, path, name='name'):
        self.path = path
        self.name = name
        super().__init__()

    def get_aggregation(self):
        return A(
            'nested',
            path=self.path,
            aggs={
                'inner': A('multi_terms', terms=[
                    {'field': f'{self.path}.{self.name}'},
                    {'field': f'{self.path}.id'}
                ])
            }
        )

    def get_values(self, data, filter_values):
        result = super().get_values(data.inner, filter_values)
        return result

    def add_filter(self, filter_values):
        if filter_values:
            return Nested(
                path=self.path,
                query=Terms(**{f'{self.path}__id': filter_values})
            )


class FilteredNestedFacet(Facet):
    def __init__(self, path, filter, name='name'):
        self.path = path
        self.filter = filter
        self.name = name
        super().__init__()

    def get_aggregation(self):
        return A(
            'nested',
            path=self.path,
            aggs={
                'filter': A(
                    'filter',
                    filter=Term(**self.filter),
                    aggs={
                        'inner': A('multi_terms', terms=[
                            {'field': f'{self.path}.{self.name}'},
                            {'field': f'{self.path}.id'}
                        ])
                    }
                )
            }
        )

    def get_values(self, data, filter_values):
        result = super().get_values(data.filter.inner, filter_values)
        return result

    def add_filter(self, filter_values):
        if filter_values:
            return Nested(
                path=self.path,
                query=Terms(**{f'{self.path}__id': filter_values})
            )

    def is_filtered(self, key, filter_values):
        return key[-1] in filter_values


class TranslatedFacet(FilteredNestedFacet):
    def __init__(self, path, name='name'):
        super().__init__(
            path,
            {f'{path}.language': get_current_language()},
            name
        )


class SegmentFacet(FilteredNestedFacet):
    def __init__(self, segment_type):
        super().__init__('segments', {'segments.type': segment_type.slug})


class ActivitySearch(FacetedSearch):
    doc_types = [Activity]
    fields = [
        'title^3', 'description^2', 'initiative.title^2', 'initiative.story', 'initiative.pitch',
        'slots.title', 'theme.name', 'categories.name'
    ]

    facets = {
        'upcoming': TermsFacet(field='is_upcoming'),
        'activity-type': TermsFacet(field='activity_type'),
    }

    possible_facets = {
        'team_activity': TermsFacet(field='team_activity'),
        'theme': TranslatedFacet('theme'),
        'category': TranslatedFacet('categories', 'title'),
        'skill': TranslatedFacet('expertise'),
        'country': NamedNestedFacet('country'),
        'location': NamedNestedFacet('office'),
    }

    def __new__(cls, search, filter):
        result = super().__new__(cls)

        settings = InitiativePlatformSettings.objects.get()

        for filter in settings.activity_search_filters:
            try:
                result.facets[filter] = cls.possible_facets[filter]
            except KeyError:
                pass

        for segment_type in SegmentType.objects.all():
            result.facets[f'segment.{segment_type.slug}'] = SegmentFacet(segment_type)

        return result


class ActivitySearchFilter(ElasticSearchFilter):
    def filter_queryset(self, request, queryset, view):
        ActivitySearch.index = activity._name

        filter = {}
        regex = re.compile(r'^filter\[([\w,\-\.]+)\]$')

        for key, value in request.GET.items():
            match = regex.match(key)
            filter_name = match.groups()[0]
            if match and filter_name != 'search':
                filter[filter_name] = value

        search = request.GET.get('filter[search]')

        return ActivitySearch(search, filter)
