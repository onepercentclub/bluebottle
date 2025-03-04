from django_tools.middlewares.ThreadLocal import get_current_user
from elasticsearch_dsl import Facet
from elasticsearch_dsl.faceted_search import TermsFacet
from elasticsearch_dsl.query import Term, MatchNone, Terms, MatchAll
from rest_framework.exceptions import NotAuthenticated

from bluebottle.activities.filters import UntranslatedModelFacet, BooleanFacet
from bluebottle.categories.models import Category
from bluebottle.geo.models import Country, Location
from bluebottle.initiatives.documents import initiative
from bluebottle.initiatives.models import InitiativePlatformSettings, Theme
from bluebottle.offices.models import OfficeSubRegion, OfficeRegion
from bluebottle.segments.models import SegmentType
from bluebottle.utils.filters import (
    ElasticSearchFilter, Search, SegmentFacet, ModelFacet
)

from elasticsearch_dsl.aggs import A
from django.utils.translation import gettext_lazy as _


class OwnerFacet(TermsFacet):
    def __init__(self, **kwargs):
        super().__init__(field='owner', **kwargs)

    def add_filter(self, filter_values):
        if filter_values:
            user = get_current_user()
            if user.is_authenticated:
                return Term(owner=user.pk)
            raise NotAuthenticated

    def get_values(self, data, filter_values):
        return []


class StatusFacet(Facet):
    agg_type = 'terms'

    def get_aggregation(self):
        return A('filter', filter=MatchAll())

    def get_values(self, data, filter_values):
        return A('filter', filter=MatchNone())

    def add_filter(self, filter_values):
        if filter_values == ['draft']:
            return Terms(status=['draft', 'needs_work'])
        if filter_values == ['open']:
            return Terms(status=['approved'])
        if filter_values == ['failed']:
            return Terms(status=['rejected', 'deleted', 'cancelled'])
        return MatchNone()


class OfficeFacet(ModelFacet):
    def __init__(self):
        super().__init__('location', Location)

    @property
    def filter(self):
        return MatchAll()


class OpenFacet(BooleanFacet):

    def __init__(self, *args, **kwargs):

        labels = {
            True: _('Open initiatives'),
            False: _('Closed initiatives')
        }
        super().__init__(*args, labels=labels, field='is_open', **kwargs)

    def get_value(self, bucket):
        return (self.labels[bucket["key"]], bucket["key"])


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
        'status': StatusFacet(),
    }

    possible_facets = {
        'theme': ModelFacet('theme', Theme),
        'category': ModelFacet('categories', Category, 'title'),
        'country': ModelFacet('country', Country),
        'office': OfficeFacet(),
        'office_subregion': UntranslatedModelFacet('office_subregion', OfficeSubRegion),
        'office_region': UntranslatedModelFacet('office_region', OfficeRegion),
        'open': OpenFacet(),
    }

    def __new__(cls, *args, **kwargs):
        settings = InitiativePlatformSettings.objects.get()
        result = super().__new__(cls, settings.search_filters_initiatives.all())

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
