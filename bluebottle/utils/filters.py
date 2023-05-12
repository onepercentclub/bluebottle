import re

import dateutil
from elasticsearch_dsl import (
    FacetedSearch, Facet
)
from elasticsearch_dsl.aggs import Bucket, A
from elasticsearch_dsl.query import (
    Terms, Term, Nested, MultiMatch, Bool, Range, MatchAll
)
from rest_framework import filters

from bluebottle.utils.utils import get_current_language


class TrigramFilter(filters.SearchFilter):

    def construct_search(self, field_name):
        return "%s__unaccent__trigram_similar" % field_name

    def get_search_terms(self, request):
        """
        Don't split into separate search terms
        """
        search = request.query_params.get(self.search_param, None)
        if search:
            return [search]
        return None


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

    def get_values(self, data, filter_values):
        values = super().get_values(data, filter_values)
        return [
            ((value[0][0], f'segments.{value[0][1]}'), value[1], value[2]) for value in values
        ]


class DateRangeFacet(Facet):
    def get_aggregation(self):
        return A('filter', filter=MatchAll())

    def get_values(self, data, filter_values):
        return []

    def get_value_filter(self, filter_value):
        start, end = filter_value.split(',')
        return Range(
            _expand__to_dot=False,
            **{
                self._params["field"]: {
                    "gte": dateutil.parser.parse(start),
                    "lt": dateutil.parser.parse(end)
                }
            }
        )


class Search(FacetedSearch):
    def __new__(cls, enabled_filters):
        result = super().__new__(cls)

        for filter in enabled_filters:
            try:
                result.facets[filter] = cls.possible_facets[filter]
            except KeyError:
                pass

        return result

    def __init__(self, query=None, filters={}, sort=(), user=None):
        self.user = user
        self.index = self.doc_types[0]._name

        super().__init__(query, filters, sort)

    @property
    def default_sort(self):
        return list(self.sorting.keys())[0]

    def sort(self, search):
        """
        Add sorting information to the request.
        """
        sort = self._sort or self.default_sort

        return search.sort(*self.sorting[sort])

    def highlight(self, search):
        return search

    def query(self, search, query):
        if query:
            queries = []
            for path, fields in self.fields:
                if path:
                    queries.append(
                        Nested(
                            path=path,
                            query=MultiMatch(
                                fields=[f'{path}.{field}' for field in fields],
                                query=query
                            )
                        )
                    )
                else:
                    queries.append(
                        MultiMatch(
                            fields=fields, query=query
                        )

                    )

            return search.query(Bool(should=queries))
        else:
            return search


class ElasticSearchFilter(filters.SearchFilter):
    def filter_queryset(self, request, queryset, view):
        filter = {}
        regex = re.compile(r'^filter\[([\w,\-\.]+)\]$')

        for key, value in request.GET.items():
            match = regex.match(key)
            if match and match.groups()[0] != 'search':
                filter[match.groups()[0]] = value

        search = request.GET.get('filter[search]')

        return self.search_class(search, filter, request.GET.get('sort'), user=request.user)
