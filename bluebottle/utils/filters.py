import re

import dateutil
from elasticsearch_dsl import (
    FacetedSearch, Facet
)
from elasticsearch_dsl.aggs import A
from elasticsearch_dsl.query import (
    Terms, Term, Nested, MultiMatch, Bool, Range, MatchAll
)
from rest_framework import filters
from rest_framework.filters import BaseFilterBackend

from bluebottle.segments.models import Segment
from bluebottle.utils.utils import get_current_language

FACET_LIMIT = 10000


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


class ModelFacet(Facet):
    def __init__(self, path, model, attr='name'):
        self.path = path
        self.model = model
        self.attr = attr
        super().__init__()

    @property
    def filter(self):
        return Term(**{f'{self.path}.language': get_current_language()})

    def get_aggregation(self):
        return A(
            'nested',
            path=self.path,
            aggs={
                'filter': A(
                    'filter',
                    filter=self.filter,
                    aggs={
                        'inner': A('terms', size=FACET_LIMIT, field=f"{self.path}.id")
                    }
                )
            }
        )

    def get_values(self, data, filter_values):
        result = super().get_values(data.filter.inner, filter_values)
        ids = [facet[0] for facet in result]

        if filter_values and filter_values[0] not in ids and filter_values[0].isnumeric():
            result.append((filter_values[0], 0, True))
            ids.append(filter_values[0])

        models = dict(
            (str(model.pk), model)
            for model in self.model.objects.filter(pk__in=ids)
        )
        result = [
            ((getattr(models[id], self.attr), id), count, active)
            for (id, count, active) in result
        ]
        return result

    def add_filter(self, filter_values):
        if filter_values:
            return Nested(
                path=self.path,
                query=Terms(**{f'{self.path}.id': filter_values})
            )


class SegmentFacet(ModelFacet):
    def __init__(self, segment_type):
        self.segment_type = segment_type
        super().__init__('segments', Segment)

    @property
    def filter(self):
        return Term(**{'segments.type': self.segment_type.slug})


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

        # Make sure that we copy the original facets, so that things do not add up
        facets = dict(**result.facets)

        for filter in enabled_filters:
            try:
                facets[filter.type] = cls.possible_facets[filter.type]
            except KeyError:
                pass

        result.facets = facets

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

        return search.sort(*self.sorting.get(sort, self.sorting[self.default_sort]))

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
                                type="phrase_prefix",
                                query=query
                            )
                        )
                    )
                else:
                    queries.append(
                        MultiMatch(
                            fields=fields,
                            query=query,
                            type="phrase_prefix"
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
            if value and match and match.groups()[0] != 'search':
                filter[match.groups()[0]] = value

        search = request.GET.get('filter[search]')

        return self.search_class(search, filter, request.GET.get('sort'), user=request.user)


class SearchFilterBackend(BaseFilterBackend):
    """
    A custom filter backend that supports filtering using `filter[fieldname]=value`.
    """

    def filter_queryset(self, request, queryset, view):
        # Get all query parameters that start with "filter["
        filter_params = {key[7:-1]: value for key, value in request.GET.items() if
                         key.startswith('filter[') and key.endswith(']')}

        # Apply the filters dynamically to the queryset
        if filter_params:
            queryset = queryset.filter(**filter_params)

        return queryset
