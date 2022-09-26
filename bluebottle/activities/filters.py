import re
import dateutil
from datetime import datetime, time

from django.conf import settings

from elasticsearch_dsl.query import (
    FunctionScore, SF, Terms, Term, Nested, Q, Range, ConstantScore
)
from elasticsearch_dsl.function import ScriptScore
from bluebottle.activities.documents import activity
from bluebottle.utils.filters import ElasticSearchFilter


class ActivitySearchFilter(ElasticSearchFilter):
    document = activity

    sort_fields = {
        'highlight': ('-highlight', ),
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
        'categories.id',
        'expertise.id',
        'type',
        'status',
        'upcoming',
        'location.id',
        'segment',
        'team_activity',
        'initiative.id',
        'highlight',
    )

    search_fields = (
        'status',
        'title',
        'description',
        'owner.full_name',
        'initiative.title',
        'initiative.pitch',
        'location.name',
        'location.city',
        'segments.name',
    )

    boost = {
        'title': 2,
        'initiative.pitch': 0.5,
        'initiative.story': 0.5,
        'location.name': 0.5,
        'location.city': 0.5,
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
                            'lat': location.position.y,
                            'lon': location.position.x
                        },
                    )
                )

            score = score | (Q('terms', status=['open', 'running', 'full']) & matching)

        return score

    def get_type_filter(self, value, request):
        if value == 'time_based':
            return Term(type='dateactivity') | Term(type='periodactivity')

        return Term(type=value)

    def get_upcoming_filter(self, value, request):
        if value == 'true':
            return Terms(status=['open', 'full'])
        if value == 'false':
            return Terms(status=['succeeded', 'partially_funded'])

    def get_duration_filter(self, value, request):
        start = request.GET.get('filter[start]')
        end = request.GET.get('filter[end]')

        try:
            start_date = dateutil.parser.parse(start) if start else None
            end_date = datetime.combine(dateutil.parser.parse(end), time.max) if end else None
            if start_date and end_date and end_date < start_date:
                # If start end date if before start date, the return no results
                return Term(id=0)
            return Range(
                duration={
                    'gte': dateutil.parser.parse(start) if start else None,
                    'lte': datetime.combine(dateutil.parser.parse(end), time.max) if end else None,
                }
            )
        except ValueError:
            return None

    def get_filter_fields(self, request):
        fields = super().get_filter_fields(request)

        if request.GET.get('filter[start]') or request.GET.get('filter[end]'):
            fields = fields + ['duration']

        return fields

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

        filters = [
            ~Terms(status=[
                'draft', 'needs_work', 'submitted', 'deleted',
                'closed', 'cancelled', 'rejected'
            ]),
        ]

        fields = super(ActivitySearchFilter, self).get_filter_fields(request)
        if 'initiative.id' in fields and request.user.is_authenticated:
            filters = [
                ~Terms(status=[
                    'draft', 'needs_work', 'submitted', 'deleted',
                    'closed', 'cancelled', 'rejected'
                ]) |
                Nested(
                    path='owner',
                    query=(
                        Term(owner__id=request.user.id)
                    )
                ) |
                Nested(
                    path='initiative',
                    query=(
                        Term(initiative__owner=request.user.id)
                    )
                ) |
                Nested(
                    path='initiative.activity_managers',
                    query=(
                        Term(initiative__activity_managers__id=request.user.id)
                    )
                )
            ]
        else:
            filters = [
                ~Terms(status=[
                    'draft', 'needs_work', 'submitted', 'deleted',
                    'closed', 'cancelled', 'rejected'
                ]),
            ]

        if not request.user.is_staff:
            filters += [
                ~Nested(
                    path='segments',
                    query=(
                        Term(segments__closed=True)
                    )
                ) | Nested(
                    path='segments',
                    query=(
                        Terms(
                            segments__id=[
                                segment.id for segment in request.user.segments.filter(closed=True)
                            ] if request.user.is_authenticated else []
                        )
                    )
                )
            ]

        if not request.user.has_perm(permission):
            return filters + [
                Nested(
                    path='owner',
                    query=Term(owner__id=request.user.pk)
                ),
            ]
        else:
            return filters
