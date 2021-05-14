import re
import dateutil

from django.db.models import Q as DQ
from django.conf import settings

from django_filters.rest_framework import DjangoFilterBackend
from elasticsearch_dsl.query import (
    FunctionScore, SF, Terms, Term, Nested, Q, Range, ConstantScore
)
from elasticsearch_dsl.function import ScriptScore
from bluebottle.activities.documents import activity
from bluebottle.activities.states import ActivityStateMachine
from bluebottle.time_based.states import TimeBasedStateMachine
from bluebottle.funding.states import FundingStateMachine
from bluebottle.utils.filters import ElasticSearchFilter


class ActivitySearchFilter(ElasticSearchFilter):
    document = activity

    sort_fields = {
        'date': ('-activity_date', ),
        'alphabetical': ('title_keyword', ),
        'popularity': 'relevancy',
        'relevancy': 'relevancy',
    }
    default_sort_field = 'relevancy'

    filters = (
        'owner.id',
        'theme.id',
        'country',
        'categories.slug',
        'expertise.id',
        'type',
        'status',
        'start',
        'end',
        'initiative_location.id',
        'segment',
    )

    search_fields = (
        'status',
        'title',
        'description',
        'owner.full_name',
        'initiative.title',
        'initiative.pitch',
        'initiative.pitch',
        'initiative_location.name',
        'initiative_location.city',
        'location.formatted_address',
        'segments.name',
    )

    boost = {
        'title': 2,
        'initiative.pitch': 0.5,
        'initiative.story': 0.5,
        'initiative_location.name': 0.5,
        'initiative_location.city': 0.5,
    }

    def get_sort_relevancy(self, request):
        score = FunctionScore(
            score_mode='sum',
            functions=[
                SF(
                    'field_value_factor',
                    field='status_score',
                    weight=10,
                )
            ],
        )
        score = score | FunctionScore(
            score_mode='first',
            functions=[
                SF(
                    'gauss',
                    weight=0.1,
                    filter=Q('exists', field='activity_date'),
                    activity_date={
                        'scale': "10d"
                    },
                ),
                ScriptScore(script="0")
            ]
        )

        score = score | FunctionScore(
            score_mode='sum',
            functions=[
                SF(
                    'field_value_factor',
                    field='donation_count',
                    weight=0.002,
                ),
            ]
        )

        if request.user.is_authenticated:
            matching = ConstantScore(
                boost=0.5,
                filter=Nested(
                    path='theme',
                    query=Q(
                        'terms',
                        theme__id=[
                            theme.pk for theme in request.user.favourite_themes.all()
                        ]
                    )
                )
            ) | ConstantScore(
                filter=Nested(
                    path='expertise',
                    query=Q(
                        'terms',
                        expertise__id=[
                            skill.pk for skill in request.user.skills.all()
                        ]
                    )
                )
            ) | ConstantScore(
                boost=0.75,
                filter=~Nested(
                    path='expertise',
                    query=Q(
                        'exists',
                        field='expertise.id'
                    )
                )
            ) | ConstantScore(
                boost=0.9,
                filter=Q('term', is_online=True)
            )

            location = request.user.location or request.user.place
            if location and location.position:
                matching = matching | ConstantScore(
                    filter=Q(
                        'geo_distance',
                        distance='{}000m'.format(settings.MATCHING_DISTANCE),
                        position={
                            'lat': location.position.latitude,
                            'lon': location.position.longitude
                        },
                    )
                )

            score = score | (Q('terms', status=['open', 'running', 'full']) & matching)

        return score

    def get_type_filter(self, value, request):
        if value == 'time_based':
            return Term(type='dateactivity') | Term(type='periodactivity')

        return Term(type=value)

    def get_start_filter(self, value, request):
        try:
            date = dateutil.parser.parse(value).date()
        except ValueError:
            return None
        return Range(end={'gte': date}) | ~Q('exists', field='end')

    def get_end_filter(self, value, request):
        try:
            date = dateutil.parser.parse(value).date()
        except ValueError:
            return None
        return Range(start={'lt': date}) | ~Q('exists', field='start')

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
                ~Terms(status=[
                    'draft', 'needs_work', 'submitted', 'deleted',
                    'closed', 'cancelled', 'rejected'
                ])
            ]
        else:
            return [
                ~Terms(status=[
                    'draft', 'needs_work', 'submitted', 'deleted', 'closed', 'cancelled',
                    'rejected',
                ])
            ]


class ActivityFilter(DjangoFilterBackend):
    """
    Filter that shows only successful contributors
    """
    public_statuses = [
        ActivityStateMachine.succeeded.value,
        ActivityStateMachine.open.value,
        TimeBasedStateMachine.full.value,
        FundingStateMachine.partially_funded.value,
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
