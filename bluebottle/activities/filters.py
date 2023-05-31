from django.utils.translation import gettext_lazy as _
from elasticsearch_dsl import TermsFacet, Facet
from elasticsearch_dsl.aggs import A
from elasticsearch_dsl.query import Term, Terms, Nested, MatchAll, GeoDistance

from bluebottle.activities.documents import activity
from bluebottle.geo.models import Location, Place
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
        pk, distance, include_online = filter_value.split(':')

        if pk:
            place = Place.objects.get(pk=pk)
            if place and distance:
                geo_filter = GeoDistance(
                    _expand__to_dot=False,
                    distance=distance + 'km',
                    position={
                        'lat': float(place.position[0]),
                        'lon': float(place.position[1]),
                    }
                )
                if include_online == 'with_online':
                    return geo_filter | Term(is_online=True)
                return geo_filter
        if include_online == 'without_online':
            return Term(is_online=False)


class OfficeRestrictionFacet(Facet):
    def get_aggregation(self):
        return A('filter', filter=MatchAll())

    def get_values(self, data, filter_values):
        return []

    def get_value_filter(self, filter_value):
        office = Location.objects.get(pk=filter_value)

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
        self.label_no = label_no or _('None')
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


class TeamActivityFacet(BooleanFacet):

    def get_value(self, bucket):
        if bucket["key"] == 'teams':
            return (_("Teams"), 'teams')
        return (_('Individuals'), 'individuals')


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
        'upcoming': TermsFacet(field='is_upcoming'),
        'activity-type': TermsFacet(field='activity_type'),
        'highlight': TermsFacet(field='highlight'),
        'distance': DistanceFacet(),
        'office_restriction': OfficeRestrictionFacet(),
        'is_online': BooleanFacet(field='is_online', label_no=_('In person'), label_yes=_('Online')),
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
            lat, lon, distance, include_online = self.filter_values['distance'][0].split(':')
            if lat and lon and lat != 'undefined' and lon != 'undefined':
                geo_sort = {
                    "_geo_distance": {
                        "position": {
                            "lat": float(lat),
                            "lon": float(lon),
                        },
                        "order": "asc",
                        "distance_type": "arc"
                    }
                }

                if include_online == 'with_online':
                    search = search.sort(
                        {"is_online": {"order": "desc"}},
                        geo_sort
                    )
                else:
                    search = search.sort(geo_sort)
            else:
                if include_online == 'with_online':
                    search = search.sort(
                        {"is_online": {"order": "desc"}}
                    )

        elif 'upcoming' in self.filter_values and self.filter_values['upcoming']:
            if 'date' in self.filter_values:
                start = self.filter_values['date'][0].split(',')[0]
            else:
                start = 'now'
            search = search.sort({
                "dates.start": {
                    "order": "asc",
                    "nested_path": "dates",
                    "nested_filter": {
                        "range": {
                            "dates.start": {
                                "gte": start
                            }
                        }
                    }

                }
            }, {
                "dates.end": {
                    "order": "asc",
                    "nested_path": "dates",
                    "nested_filter": {
                        "range": {
                            "dates.end": {
                                "gte": start
                            }
                        }
                    }

                }
            })

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

        return search


class ActivitySearchFilter(ElasticSearchFilter):
    index = activity
    search_class = ActivitySearch
