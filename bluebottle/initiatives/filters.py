import re
from elasticsearch_dsl import Q
from elasticsearch_dsl.query import Term, Nested, Terms

from bluebottle.utils.filters import ElasticSearchFilter
from bluebottle.initiatives.documents import InitiativeDocument


class InitiativeSearchFilter(ElasticSearchFilter):
    document = InitiativeDocument

    sort_fields = {
        'date': ('-created', ),
        'activity_date': ({
            'activities.status_score': {
                'order': 'desc',
                'mode': 'max',
                'nested': {
                    'path': 'activities'
                }
            },
            'activities.activity_date': {
                'order': 'desc',
                'mode': 'max',
                'nested': {
                    'path': 'activities'
                }
            }
        }, ),
        'alphabetical': ('title_keyword', ),
    }
    default_sort_field = 'date'

    filters = (
        'owner.id',
        'activity_managers.id',
        'theme.id',
        'country',
        'categories.id',
        'categories.slug',
        'location.id',
        'segment',
    )

    search_fields = (
        'status', 'title', 'story', 'pitch',
        'place.locality', 'place.postal_code', 'place.formatted_address',
        'location.name', 'location.city', 'theme.name',
        'owner.full_name', 'promoter.full_name',
    )

    boost = {'title': 2}

    def get_default_filters(self, request):
        fields = super(InitiativeSearchFilter, self).get_filter_fields(request)

        permission = 'initiatives.api_read_initiative'

        public_filter = Term(status='approved') & (
            Term(has_public_activities=True) |
            Term(has_closed_activities=False) |
            Nested(
                path='segments',
                query=(
                    Terms(
                        segments__id=[
                            segment.id for segment in request.user.segments.filter(closed=True)
                        ] if request.user.is_authenticated else []
                    )
                )
            )
        )

        if not request.user.has_perm(permission):
            filters = [Term(owner_id=request.user.id)]
            if 'owner.id' not in fields:
                filters.append(public_filter)
        elif 'owner.id' in fields and request.user.is_authenticated:
            value = request.user.pk
            filters = [
                Nested(path='owner', query=Term(owner__id=value)) |
                Nested(path='promoter', query=Term(promoter__id=value)) |
                Nested(path='activity_managers', query=Term(activity_managers__id=value)) |
                Nested(path='activity_owners', query=Term(activity_owners__id=value)) |
                public_filter
            ]
        else:
            filters = [public_filter]

        return filters

    def get_filters(self, request):
        filters = super(InitiativeSearchFilter, self).get_filters(request)
        regex = re.compile('^filter\[segment\.(?P<type>[\w\-]+)\]$')
        for key, value in list(request.GET.items()):
            matches = regex.match(key)
            if matches:
                filters.append(
                    Nested(
                        path='segments',
                        query=Term(
                            segments__segment_type=matches.groupdict()['type']
                        ) & Term(
                            segments__id=value
                        )
                    )
                )

        return filters

    def get_filter(self, request, field):
        # Also return activity_manger.id when filtering on owner.id
        if field == 'owner.id':
            value = request.GET['filter[{}]'.format(field)]
            return Q(
                Nested(path='owner', query=Term(**{field: value})) |
                Nested(path='promoter', query=Term(promoter__id=value)) |
                Nested(path='activity_owners', query=Term(activity_owners__id=value)) |
                Nested(path='activity_managers', query=Term(activity_managers__id=value))
            )

        regex = re.compile('^filter\[segment\.(?P<type>[\w\-]+)\]$')
        matches = regex.match(field)

        if matches:
            value = request.GET['filter[{}]'.format(field)]

            return Nested(
                path='segments',
                query=Term(
                    segments__type=matches.groupdict()['type']
                ) & Term(
                    segments__id=value
                )
            )

        return super(InitiativeSearchFilter, self).get_filter(request, field)
