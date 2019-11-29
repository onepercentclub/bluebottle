import dateutil
from django_filters.rest_framework import DjangoFilterBackend

from elasticsearch_dsl.query import FunctionScore, SF, Terms, Term, Nested, Q, Range
from django.db.models import Q as DQ

from bluebottle.activities.transitions import ActivityTransitions
from bluebottle.events.transitions import EventTransitions
from bluebottle.funding.transitions import FundingTransitions
from bluebottle.utils.filters import ElasticSearchFilter
from bluebottle.activities.documents import activity


class ActivitySearchFilter(ElasticSearchFilter):
    document = activity

    sort_fields = {
        'date': ('-created', ),
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
    )

    search_fields = (
        'status', 'title', 'description', 'owner.full_name',
        'initiative.title', 'initiative.pitch', 'initiative.pitch',
        'initiative_location.name', 'initiative_location.city',
        'location.formatted_address',
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
                    factor=1
                ),
                SF(
                    'gauss',
                    weight=0.001,
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
                    weight=0.01,
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
                            'weight': 0.1,
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
                            'weight': 0.1,
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
                            'weight': 0.1,
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
        return Range(date={'gt': start, 'lt': end}) | Range(deadline={'gt': start})

    def get_default_filters(self, request):
        permission = 'activities.api_read_activity'
        if not request.user.has_perm(permission):
            return [
                Nested(
                    path='owner',
                    query=Term(owner__id=request.user.pk)
                ),
                Terms(review_status=['approved']),
                ~Term(status='closed')
            ]
        else:
            return [Terms(review_status=['approved']), ~Term(status='closed')]


class ActivityFilter(DjangoFilterBackend):
    """
    Filter that shows only successful contributions
    """
    public_statuses = [
        ActivityTransitions.values.succeeded,
        ActivityTransitions.values.open,
        FundingTransitions.values.partially_funded,
        EventTransitions.values.full,
        EventTransitions.values.running
    ]

    def filter_queryset(self, request, queryset, view):
        if request.user.id:
            queryset = queryset.filter(
                DQ(owner=request.user) |
                DQ(initiative__activity_manager=request.user) |
                DQ(initiative__owner=request.user) |
                DQ(status__in=self.public_statuses)
            )
        else:
            queryset = queryset.filter(status__in=self.public_statuses)

        return super(ActivityFilter, self).filter_queryset(request, queryset, view)
