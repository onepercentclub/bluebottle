from datetime import datetime

import dateutil
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_tools.middlewares.ThreadLocal import get_current_request, get_current_user
from elasticsearch_dsl import Facet, Q, TermsFacet
from elasticsearch_dsl.aggs import A
from elasticsearch_dsl.query import (
    GeoDistance,
    MatchAll,
    MatchNone,
    Nested,
    Range,
    Exists,
    Term,
    Bool,
    Terms,
)
from pytz import UTC

from bluebottle.activities.documents import activity
from bluebottle.categories.models import Category
from bluebottle.geo.models import Country, Location, Place
from bluebottle.initiatives.models import InitiativePlatformSettings, Theme
from bluebottle.offices.models import OfficeRegion, OfficeSubRegion
from bluebottle.segments.models import SegmentType
from bluebottle.time_based.models import Skill
from bluebottle.utils.filters import (
    ElasticSearchFilter,
    ModelFacet,
    Search,
    SegmentFacet,
)


class DistanceFacet(Facet):
    def get_aggregation(self):
        return A("filter", filter=MatchAll())

    def get_values(self, data, filter_values):
        return []

    def get_value_filter(self, filter_value):
        request = get_current_request()

        place_id = request.GET.get("place")
        if place_id:
            place = Place.objects.filter(pk=place_id).first()
            if place and place.position and filter_value:
                geo_filter = GeoDistance(
                    _expand__to_dot=False,
                    distance=filter_value,
                    position={
                        "lat": float(place.position[1]),
                        "lon": float(place.position[0]),
                    },
                )
                return geo_filter | Term(is_online=True)


class OfficeRestrictionFacet(Facet):
    def get_aggregation(self):
        return A("filter", filter=MatchAll())

    def get_values(self, data, filter_values):
        return []

    def get_value_filter(self, filter_value):
        user = get_current_user()
        if filter_value == "0" or not user.is_authenticated or not user.location:
            return
        office = user.location
        query = Term(office_restriction__restriction="all") | (
            Term(office_restriction__office=office.id)
            & Term(office_restriction__restriction="office")
        )

        if office.subregion:
            query = query | (
                Term(office_restriction__subregion=office.subregion.id)
                & Term(office_restriction__restriction="office_subregion")
            )

            if office.subregion.region:
                query = query | (
                    Term(office_restriction__region=office.subregion.region.id)
                    & Term(office_restriction__restriction="office_region")
                )

        return Nested(path="office_restriction", query=query)


class UpcomingFacet(Facet):
    agg_type = "terms"

    def get_aggregation(self):
        return A("filter", filter=MatchAll())

    def get_values(self, data, filter_values):
        return []

    def add_filter(self, filter_values):
        if filter_values == ["1"]:
            settings = InitiativePlatformSettings.objects.get()
            statuses = ["open", "running"]
            if settings.include_full_activities:
                statuses.append("full")
            return Terms(status=statuses)
        if filter_values == ["0"]:
            return Terms(status=["succeeded", "partially_funded", "refnnded"])


class DraftFacet(Facet):
    agg_type = "terms"

    def get_aggregation(self):
        return A("filter", filter=MatchAll())

    def get_values(self, data, filter_values):
        return []

    def add_filter(self, filter_values):
        if filter_values == ["1"]:
            statuses = ["draft", "needs_work"]
            return Terms(status=statuses)


class BooleanFacet(Facet):
    agg_type = "terms"

    def __init__(self, metric=None, metric_sort="desc", labels=None, **kwargs):
        self.labels = labels or {"1": _("Yes"), "0": _("No")}

        super().__init__(metric, metric_sort, **kwargs)

    def get_value(self, bucket):
        return (self.labels[str(bucket["key"])], 1 if bucket["key"] else 0)

    def get_values(self, data, filter_values):
        result = super().get_values(data, filter_values)
        if not len(result) and len(filter_values):
            result.append(((self.labels[filter_values[0]], filter_values[0]), 0, True))

        return result

    def add_filter(self, filter_values):
        if filter_values == ["0"]:
            filter_values = [False]
        if filter_values == ["1"]:
            filter_values = [True]
        if filter_values:
            return Terms(**{self._params["field"]: filter_values})

    def is_filtered(self, key, filter_values):
        """
        Is a filter active on the given key.
        """
        return str(key[-1]) in filter_values


class TeamActivityFacet(BooleanFacet):
    def __init__(self, *args, **kwargs):
        labels = {"teams": _("With your team"), "individuals": _("As an individual")}
        super().__init__(*args, labels=labels, **kwargs)

    def get_value(self, bucket):
        return (self.labels[bucket["key"]], bucket["key"])


class MatchingFacet(BooleanFacet):

    def add_filter(self, filter_values):
        user = get_current_user()
        filters = Terms(status=["open", "full", "running"])

        if not user.is_authenticated:
            return filters

        if user.location:
            office = user.location
            office_filter = Term(office_restriction__restriction="all") | (
                Term(office_restriction__office=office.id)
                & Term(office_restriction__restriction="office")
            )

            if office.subregion:
                office_filter = office_filter | (
                    Term(office_restriction__subregion=office.subregion.id)
                    & Term(office_restriction__restriction="office_subregion")
                )

                if office.subregion.region:
                    office_filter = office_filter | (
                        Term(office_restriction__region=office.subregion.region.id)
                        & Term(office_restriction__restriction="office_region")
                    )
            filters = filters & Nested(path="office_restriction", query=office_filter)

        if user.search_distance and user.place and not user.any_search_distance:
            place = user.place
            if user.exclude_online:
                distance_filter = GeoDistance(
                    _expand__to_dot=False,
                    distance=user.search_distance,
                    position={
                        "lat": float(place.position[1]),
                        "lon": float(place.position[0]),
                    },
                )
            else:
                distance_filter = GeoDistance(
                    _expand__to_dot=False,
                    distance=user.search_distance,
                    position={
                        "lat": float(place.position[1]),
                        "lon": float(place.position[0]),
                    },
                ) | Term(is_online=True)

            filters = filters & distance_filter

        return filters


class ManagingFacet(Facet):
    agg_type = "terms"

    def get_aggregation(self):
        return A("filter", filter=MatchAll())

    def get_values(self, data, filter_values):
        return A("filter", filter=MatchNone())

    def add_filter(self, filter_values):
        if filter_values == ["1"]:
            user = get_current_user()

            if not user.is_authenticated:
                return MatchNone()
            return Term(manager=user.id)


class StatusFacet(Facet):
    agg_type = "terms"

    def get_aggregation(self):
        return A("filter", filter=MatchAll())

    def get_values(self, data, filter_values):
        return A("filter", filter=MatchNone())

    def add_filter(self, filter_values):
        if filter_values == ["draft"]:
            return Terms(status=["draft", "needs_work"])
        if filter_values == ["open"]:
            return Terms(status=["open", "running", "full", "on_hold"])
        if filter_values == ["succeeded"]:
            return Terms(status=["succeeded", "partially_funded"])
        if filter_values == ["failed"]:
            return Terms(
                status=["refunded", "rejected", "expired", "failed", "cancelled"]
            )
        return MatchNone()


class InitiativeFacet(TermsFacet):
    def __init__(self, **kwargs):
        super().__init__(field="owner", **kwargs)

    def add_filter(self, filter_values):
        initiative_filter = Nested(
            path="initiative", query=(Terms(initiative__id=filter_values))
        )
        open_filter = Terms(status=["succeeded", "open", "full", "partially_funded"])
        user = get_current_user()
        if user.is_authenticated:
            return (
                initiative_filter
                & (Term(manager=user.id) | open_filter)
                & ~Terms(status=["deleted"])
            )
        return initiative_filter & open_filter


class ActivityDateRangeFacet(Facet):
    def get_aggregation(self):
        return A("filter", filter=MatchAll())

    def get_values(self, data, filter_values):
        return []

    def get_value_filter(self, filter_value):
        start, end = filter_value.split(",")
        start = dateutil.parser.parse(start)
        end = dateutil.parser.parse(end)

        if start.astimezone(UTC) >= now():
            return Range(
                _expand__to_dot=False, **{"duration": {"gte": start, "lt": end}}
            )
        else:
            return Q(
                "nested",
                path="dates",
                query=Q("range", **{"dates.end": {"gt": start, "lt": end}}),
            )


class UntranslatedModelFacet(ModelFacet):
    @property
    def filter(self):
        return MatchAll()


class ActivitySearch(Search):
    doc_types = [activity]

    sorting = {
        "date": ["dates.start"],
        "created": ["created"],
        "distance": ["distance"],
    }
    default_sort = "date"

    fields = [
        (None, ("title^3", "description^2")),
        ("initiative", ("title^2", "story", "pitch")),
        ("slots", ("title",)),
    ]

    facets = {
        "initiative.id": InitiativeFacet(),
        "upcoming": UpcomingFacet(),
        "draft": DraftFacet(),
        "activity-type": TermsFacet(field="activity_type", min_doc_count=0),
        "status": TermsFacet(field="status"),
        "matching": MatchingFacet(field="matching"),
        "highlight": BooleanFacet(field="highlight"),
        "distance": DistanceFacet(),
        "office_restriction": OfficeRestrictionFacet(),
        "is_online": BooleanFacet(
            field="is_online", labels={"0": _("In-person"), "1": _("Online/remote")}
        ),
        "team_activity": TeamActivityFacet(field="team_activity"),
        "date": ActivityDateRangeFacet(),
        "office": UntranslatedModelFacet("office", Location),
        "office_subregion": UntranslatedModelFacet("office_subregion", OfficeSubRegion),
        "office_region": UntranslatedModelFacet("office_region", OfficeRegion),
    }

    possible_facets = {
        "status": StatusFacet(),
        "managing": ManagingFacet(),
        "category": ModelFacet("categories", Category, "title"),
        "skill": ModelFacet("expertise", Skill),
        "country": ModelFacet("country", Country),
        "theme": ModelFacet("theme", Theme),
    }

    def sort(self, search):
        search = super().sort(search)

        if self._sort == "-created":
            search = search.sort(
                {
                    "created": {
                        "order": "desc",
                    }
                }
            )
            return search

        if self._sort == "distance":
            request = get_current_request()
            place_id = request.GET.get("place")
            if place_id:
                place = Place.objects.filter(pk=place_id).first()
                if place and place.position:
                    geo_sort = {
                        "_geo_distance": {
                            "position": {
                                "lat": float(place.position[1]),
                                "lon": float(place.position[0]),
                            },
                            "order": "asc",
                            "distance_type": "arc",
                        }
                    }

                    search = search.sort({"is_online": {"order": "desc"}}, geo_sort)
            else:
                search = search.sort({"is_online": {"order": "desc"}})

        if self._sort == "start":
            # Used for activity tab in initiatives
            start = now()
            end = datetime.max

            search = search.sort(
                {
                    "dates.end": {
                        "order": "asc",
                        "mode": "min",
                        "nested": {
                            "path": "dates",
                            "filter": (
                                Range(**{"dates.end": {"lte": end}})
                                & Range(**{"dates.end": {"gte": start}})
                            ),
                        },
                    }
                }
            )
            return search

        if self._sort == "date" or not self._sort:
            if (
                "upcoming" in self.filter_values
                and self.filter_values["upcoming"][0] == "1"
            ):
                start = now()
                end = None

                if "date" in self.filter_values:
                    start, end = self.filter_values["date"][0].split(",")

                search = search.sort(
                    {
                        "dates.end": {
                            "order": "asc",
                            "missing": "_last",
                            "nested": {
                                "path": "dates",
                                "filter": (
                                    Range(**{"dates.end": {"lte": end}}) &
                                    (
                                        Range(**{"dates.start": {"gte": start}}) |
                                        Bool(must_not=Exists(field='dates.start'))
                                    )
                                ),
                            },
                        },
                    }
                )
            else:
                start = datetime.min
                end = now()

                if "date" in self.filter_values:
                    start, end = self.filter_values["date"][0].split(",")

                search = search.sort(
                    {
                        "dates.end": {
                            "order": "desc",
                            "mode": "max",
                            "nested": {
                                "path": "dates",
                                "filter": (
                                    Range(**{"dates.end": {"lte": end}})
                                    & Range(**{"dates.end": {"gte": start}})
                                ),
                            },
                        }
                    }
                )
                return search

        return search

    def __new__(cls, *args, **kwargs):
        settings = InitiativePlatformSettings.objects.get()

        # Create new instance with existing search filters from settings
        result = super().__new__(
            cls, settings.search_filters_activities.distinct().all()
        )

        # get filters from the request
        filters = args[1] if len(args) > 1 and isinstance(args[1], dict) else {}

        # Temporarily add possible facets if they're in the request filters
        for facet_name, facet in cls.possible_facets.items():
            if facet_name in filters:
                result.facets[facet_name] = facet

        # Add segment facets
        for segment_type in SegmentType.objects.all():
            result.facets[f"segment.{segment_type.slug}"] = SegmentFacet(segment_type)

        return result

    def query(self, search, query):
        search = super().query(search, query)

        if not self.user.is_staff:
            search = search.filter(
                ~Nested(path="segments", query=(Term(segments__closed=True)))
                | Nested(
                    path="segments",
                    query=(
                        Terms(
                            segments__id=(
                                [
                                    segment.id
                                    for segment in self.user.segments.filter(
                                        closed=True
                                    )
                                ]
                                if self.user.is_authenticated
                                else []
                            )
                        )
                    ),
                )
            )

        if "initiative.id" not in self._filters and "status" not in self._filters:
            search = search.filter(
                Terms(
                    status=["succeeded", "open", "full", "partially_funded", "refunded"]
                )
            )

        return search


class ActivitySearchFilter(ElasticSearchFilter):
    index = activity
    search_class = ActivitySearch
