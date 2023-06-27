from datetime import datetime

from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_tools.middlewares.ThreadLocal import get_current_user, get_current_request
from elasticsearch_dsl import TermsFacet, Facet
from elasticsearch_dsl.aggs import A
from elasticsearch_dsl.query import Term, Terms, Nested, MatchAll, GeoDistance, Range

from bluebottle.activities.documents import activity
from bluebottle.geo.models import Place
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.segments.models import SegmentType
from bluebottle.utils.filters import (
    ElasticSearchFilter, Search, TranslatedFacet, DateRangeFacet, NamedNestedFacet,
    SegmentFacet
)


class DistanceFacet(Facet):
    def get_aggregation(self):
        return A('filter', filter=MatchAll())

    def get_values(self, data, filter_values):
        return []

    def get_value_filter(self, filter_value):
        request = get_current_request()

        place_id = request.GET.get('place')
        if place_id:
            place = Place.objects.first(pk=place_id)
            if place and place.position and filter_value:
                geo_filter = GeoDistance(
                    _expand__to_dot=False,
                    distance=f'{filter_value}km',
                    position={
                        'lat': float(place.position[1]),
                        'lon': float(place.position[0]),
                    }
                )
                return geo_filter | Term(is_online=True)


class OfficeRestrictionFacet(Facet):
    def get_aggregation(self):
        return A('filter', filter=MatchAll())

    def get_values(self, data, filter_values):
        return []

    def get_value_filter(self, filter_value):
        user = get_current_user()
        if filter_value == '0' or not user.is_authenticated or not user.location:
            return
        office = user.location
        return Nested(
            path='office_restriction',
            query=Term(
                office_restriction__restriction='all'
            ) | (
                Term(office_restriction__office=office.id) &
                Term(office_restriction__restriction='office')
            ) | (
                Term(office_restriction__subregion=office.subregion.id) &
                Term(office_restriction__restriction='office_subregion')
            ) | (
                Term(office_restriction__region=office.subregion.region.id) &
                Term(office_restriction__restriction='office_region')
            )
        )


class BooleanFacet(Facet):
    agg_type = 'terms'

    def __init__(self, metric=None, metric_sort="desc", label_yes=None, label_no=None, **kwargs):
        self.label_yes = label_yes or _('Yes')
        self.label_no = label_no or _('No')

        super().__init__(metric, metric_sort, **kwargs)

    def get_value(self, bucket):
        if bucket["key"]:
            return (self.label_yes, 1)
        return (self.label_no, 0)

    def add_filter(self, filter_values):
        if filter_values == ['0']:
            filter_values = [False]
        if filter_values == ['1']:
            filter_values = [True]
        if filter_values:
            return Terms(
                **{self._params["field"]: filter_values}
            )

    def is_filtered(self, key, filter_values):
        """
        Is a filter active on the given key.
        """
        return str(key[-1]) in filter_values


class TeamActivityFacet(BooleanFacet):

    def get_value(self, bucket):
        if bucket["key"] == 'teams':
            return (_("With your team"), 'teams')
        return (_('As an individual'), 'individuals')


class ActivitySearch(Search):
    doc_types = [activity]

    sorting = {
        'date': ['dates.start'],
        'distance': ['distance']
    }
    default_sort = "date"

    fields = [
        (None, ('title^3', 'description^2')),
        ('initiative', ('title^2', 'story', 'pitch')),
        ('slots', ('title',)),
    ]

    facets = {
        'upcoming': BooleanFacet(field='is_upcoming'),
        'activity-type': TermsFacet(field='activity_type'),
        'highlight': TermsFacet(field='highlight'),
        'distance': DistanceFacet(),
        'office_restriction': OfficeRestrictionFacet(),
        'is_online': BooleanFacet(field='is_online', label_no=_('In-person'), label_yes=_('Online/remote')),
        'team_activity': TeamActivityFacet(field='team_activity'),
        'office': NamedNestedFacet('office'),
    }

    possible_facets = {
        'theme': TranslatedFacet('theme'),
        'category': TranslatedFacet('categories', 'title'),
        'skill': TranslatedFacet('expertise'),
        'country': NamedNestedFacet('country'),
        'date': DateRangeFacet(field='duration'),
    }

    def sort(self, search):
        search = super().sort(search)
        if self._sort == 'distance':
            request = get_current_request()
            place_id = request.GET.get('place')
            if place_id:
                place = Place.objects.filter(pk=place_id).first()
                if place and place.position:
                    geo_sort = {
                        "_geo_distance": {
                            "position": {
                                'lat': float(place.position[1]),
                                'lon': float(place.position[0]),
                            },
                            "order": "asc",
                            "distance_type": "arc"
                        }
                    }

                    search = search.sort(
                        {"is_online": {"order": "desc"}},
                        geo_sort
                    )
            else:
                search = search.sort(
                    {"is_online": {"order": "desc"}}
                )

        if self._sort == 'date' or not self._sort:
            if 'upcoming' in self.filter_values and self.filter_values['upcoming'][0] == '1':
                start = now()
                end = datetime.max

                if 'date' in self.filter_values:
                    start, end = self.filter_values['date'][0].split(',')

                search = search.sort({
                    "dates.end": {
                        "order": "asc",
                        "nested": {
                            "path": "dates",
                            "filter": (
                                    Range(**{'dates.start': {'lte': start}}) &
                                    Range(**{'dates.end': {'gte': start}})
                            )
                        }
                    },
                    "dates.start": {
                        "order": "asc",
                        "nested": {
                            "path": "dates",
                            "filter": (
                                Range(**{'dates.start': {'lte': end}}) &
                                Range(**{'dates.end': {'gte': start}})
                            )
                        }
                    },
                })
            else:
                search = search.sort({
                    "dates.end": {
                        "order": "desc",
                        "mode": "max",
                        "nested": {
                            "path": "dates",
                        }
                    }
                })
                return search

        return search

    def __new__(cls, *args, **kwargs):
        settings = InitiativePlatformSettings.objects.get()
        result = super().__new__(cls, settings.activity_search_filters)

        for segment_type in SegmentType.objects.all():
            result.facets[f'segment.{segment_type.slug}'] = SegmentFacet(segment_type)

        return result

    def query(self, search, query):
        search = super().query(search, query)

        if not self.user.is_staff:
            search = search.filter(
                ~Nested(
                    path='segments',
                    query=(
                        Term(segments__closed=True)
                    )
                ) |
                Nested(
                    path='segments',
                    query=(

                        Terms(
                            segments__id=[
                                segment.id for segment in self.user.segments.filter(closed=True)
                            ] if self.user.is_authenticated else []
                        )
                    )
                )
            )

        search = search.filter(
            Terms(status=['succeeded', 'open', 'full', 'partially_funded'])
        )

        return search


class ActivitySearchFilter(ElasticSearchFilter):
    index = activity
    search_class = ActivitySearch
