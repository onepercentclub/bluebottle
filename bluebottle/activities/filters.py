import re
from datetime import datetime, time

import dateutil
from django.conf import settings
from elasticsearch_dsl.function import ScriptScore
from elasticsearch_dsl.query import (
    FunctionScore, SF, Terms, Term, Nested, Q, Range, ConstantScore
)

from elasticsearch_dsl import (
    FacetedSearch, NestedFacet, TermsFacet, Facet
)

from elasticsearch_dsl.aggs import Bucket

from bluebottle.activities.documents import activity, Activity
from bluebottle.geo.models import Location
from bluebottle.initiatives.models import InitiativePlatformSettings
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

class ActivitySearch(FacetedSearch):
    doc_types = [Activity]
    fields = ['title', 'description']

    facets = {
        'theme': NestedFacet(
            'theme', 
            MultiTermsFacet(terms=[{'field' :'theme.name'}, {'field' :'theme.language'}, {'field': 'theme.id'}], )
        ),
        'country': NestedFacet('country', TermsFacet(field='country.id')),
        'activity-type': TermsFacet(field='activity_type'),
    }

class ActivitySearchFilter(ElasticSearchFilter):
    def filter_queryset(self, request, queryset, view):
        ActivitySearch.index = activity._name

        filter = {}
        if 'filter[theme]' in request.GET:
            filter['theme'] = request.GET['filter[theme]']

        if 'filter[country]' in request.GET:
            filter['country'] = request.GET['filter[country]']

        if 'filter[activity-type]' in request.GET:
            filter['country'] = request.GET['filter[activity-type]']


        search = request.GET.get('filter[search]')

        return ActivitySearch(search, filter)
