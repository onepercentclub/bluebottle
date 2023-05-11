from elasticsearch_dsl import TermsFacet, Facet
from elasticsearch_dsl.aggs import A
from elasticsearch_dsl.query import Term, Terms, Nested, MatchAll, GeoDistance

from bluebottle.activities.documents import activity
from bluebottle.geo.models import Location
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
        lat, lon, distance, include_online = filter_value.split(':')
        geo_filter = GeoDistance(
            _expand__to_dot=False,
            distance=distance,
            position={
                'lat': float(lat),
                'lon': float(lon),
            }
        )
        if include_online == 'with_online':
            return geo_filter | Term(is_online=True)
        return geo_filter


class OfficeFacet(Facet):
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


class ActivitySearch(Search):
    doc_types = [activity]

    sorting = {
        'date': ['dates.start'],
        'distance': ['distance']
    }
    default_filter = "date"

    fields = [
        (None, ('title^3', 'description^2')),
        ('initiative', ('title^2', 'story', 'pitch')),
        ('slots', ('title',)),
    ]

    facets = {
        'upcoming': TermsFacet(field='is_upcoming'),
        'is_online': TermsFacet(field='is_online'),
        'activity-type': TermsFacet(field='activity_type'),
        'highlight': TermsFacet(field='highlight'),
        'distance': DistanceFacet(),
        'office_restriction': OfficeFacet(),
    }

    possible_facets = {
        'team_activity': TermsFacet(field='team_activity'),
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
            if not lat or not lon or not distance:
                if include_online == 'with_online':
                    search = search.sort(
                        {"is_online": {"order": "desc"}}
                    )
            else:
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

        elif self.filter_values['upcoming']:
            search = search.sort({
                "dates.start": {
                    "order": "asc",
                    "nested_path": "dates",
                    "nested_filter": {
                        "range": {
                            "dates.start": {
                                "gte": "now"
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
