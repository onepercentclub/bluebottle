import dateutil
import re

from django_filters.rest_framework import DjangoFilterBackend

from elasticsearch_dsl.query import FunctionScore, SF, Terms, Term, Nested, Q, Range
from django.db.models import Q as DQ

from bluebottle.activities.states import ActivityStateMachine
from bluebottle.events.states import EventStateMachine
from bluebottle.funding.states import FundingStateMachine
from bluebottle.utils.filters import ElasticSearchFilter
from bluebottle.activities.documents import activity


class ActivitySearchFilter(ElasticSearchFilter):
    document = activity

    sort_fields = {
        'date': ('-activity_date', ),
        'alphabetical': ('title_keyword', ),
        'popularity': 'popularity',
    }
    default_sort_field = 'popularity'

    filters = (
        'owner.id',
        'theme.id',
        'country',
        'categories.slug',
        'expertise.id',
        'type',
        'status',
        'date',
        'initiative_location.id',
        'segment',
    )

    search_fields = (
        'status', 'title', 'description', 'owner.full_name',
        'initiative.title', 'initiative.pitch', 'initiative.pitch',
        'initiative_location.name', 'initiative_location.city',
        'location.formatted_address', 'segments.name',
    )

    boost = {
        'title': 2,
        'initiative.pitch': 0.5,
        'initiative.story': 0.5,
        'initiative_location.name': 0.5,
        'initiative_location.city': 0.5,
    }

    def get_sort_popularity(self, request):
        score = FunctionScore(
            score_mode='sum',
            functions=[
                SF(
                    'field_value_factor',
                    field='status_score',
                    weight=10,
                    factor=10
                ),
                SF(
                    'gauss',
                    weight=0.1,
                    created={
                        'scale': "365d"
                    },
                ),
            ]
        ) | FunctionScore(
            score_mode='multiply',
            functions=[
                SF(
                    'field_value_factor',
                    field='contribution_count',
                    missing=0
                ),
                SF(
                    'gauss',
                    weight=0.1,
                    multi_value_mode='avg',
                    contributions={
                        'scale': '5d'
                    },
                ),
            ]
        )

        if request.user.is_authenticated:
            if request.user.skills:
                score = score | FunctionScore(
                    score_mode='first',
                    functions=[
                        SF({
                            'filter': Nested(
                                path='expertise',
                                query=Q(
                                    'terms',
                                    expertise__id=[skill.pk for skill in request.user.skills.all()]
                                )
                            ),
                            'weight': 1,
                        }),
                        SF({'weight': 0}),
                    ]
                )

            if request.user.favourite_themes:
                score = score | FunctionScore(
                    score_mode='first',
                    functions=[
                        SF({
                            'filter': Nested(
                                path='theme',
                                query=Q(
                                    'terms',
                                    theme__id=[theme.pk for theme in request.user.favourite_themes.all()]
                                )
                            ),
                            'weight': 1,
                        }),
                        SF({'weight': 0}),
                    ]
                )

            position = None
            if request.user.location and request.user.location.position:
                position = {
                    'lat': request.user.location.position.latitude,
                    'lon': request.user.location.position.longitude
                }
            elif request.user.place and request.user.place.position:
                position = {
                    'lat': request.user.place.position.latitude,
                    'lon': request.user.place.position.longitude
                }

            if position:
                score = score | FunctionScore(
                    score_mode='first',
                    functions=[
                        SF({
                            'filter': {'exists': {'field': 'position'}},
                            'weight': 1,
                            'gauss': {
                                'position': {
                                    'origin': position,
                                    'scale': "100km"
                                },
                                'multi_value_mode': 'max',
                            },
                        }),
                        SF({'weight': 0}),
                    ]
                )

        return score

    def get_date_filter(self, value, request):
        date = dateutil.parser.parse(value).date()
        start = date.replace(date.year, date.month, 1)
        end = start + dateutil.relativedelta.relativedelta(day=31)
        return Range(activity_date={'gte': start, 'lte': end})

    def get_filters(self, request):
        filters = super(ActivitySearchFilter, self).get_filters(request)
        regex = re.compile('^filter\[segment\.(?P<type>[\w\-]+)\]$')
        for key, value in list(request.GET.items()):
            matches = regex.match(key)
            if matches:
                filters.append(
                    Nested(
                        path='segments',
                        query=Term(
                            segments__type=matches.groupdict()['type']
                        ) & Term(
                            segments__id=value
                        )
                    )
                )

        return filters

    def get_default_filters(self, request):
        permission = 'activities.api_read_activity'
        if not request.user.has_perm(permission):
            return [
                Nested(
                    path='owner',
                    query=Term(owner__id=request.user.pk)
                ),
                ~Terms(status=['draft', 'needs_work', 'submitted', 'deleted', 'closed', 'cancelled'])
            ]
        else:
            return [
                ~Terms(status=['draft', 'needs_work', 'submitted', 'deleted', 'closed', 'cancelled'])
            ]


class ActivityFilter(DjangoFilterBackend):
    """
    Filter that shows only successful contributions
    """
    public_statuses = [
        ActivityStateMachine.succeeded.value,
        ActivityStateMachine.open.value,
        FundingStateMachine.partially_funded.value,
        EventStateMachine.full.value,
        EventStateMachine.running.value
    ]

    def filter_queryset(self, request, queryset, view):
        if request.user.id:
            queryset = queryset.filter(
                DQ(owner=request.user) |
                DQ(initiative__activity_manager=request.user) |
                DQ(initiative__owner=request.user) |
                DQ(status__in=self.public_statuses)
            ).exclude(status=ActivityStateMachine.deleted.value)
        else:
            queryset = queryset.filter(status__in=self.public_statuses)

        return super(ActivityFilter, self).filter_queryset(request, queryset, view)
