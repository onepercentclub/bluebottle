import re

import dateutil
from elasticsearch_dsl.query import FunctionScore, SF, Terms, Term, Nested, Q, Range

from bluebottle.activities.documents import activity
from bluebottle.utils.filters import ElasticSearchFilter


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
                    field='contributor_count',
                    missing=0
                ),
                SF(
                    'gauss',
                    weight=0.1,
                    multi_value_mode='avg',
                    contributors={
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
                        SF({
                            'filter': ~Nested(
                                path='expertise',
                                query=Q(
                                    'exists',
                                    field='expertise.id'
                                )
                            ),
                            'weight': 0.5,
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
                    'lat': request.user.location.position.y,
                    'lon': request.user.location.position.x
                }
            elif request.user.place and request.user.place.position:
                position = {
                    'lat': request.user.place.position.y,
                    'lon': request.user.place.position.x
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
                        SF({
                            'filter': ~Q(
                                'exists',
                                field='expertise.id'
                            ),
                            'weight': 0.5,
                        }),

                        SF({'weight': 0}),
                    ]
                )

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
