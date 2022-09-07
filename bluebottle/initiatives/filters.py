import re
from elasticsearch_dsl import Q
from elasticsearch_dsl.query import Term, Nested

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
        'segment',
    )

    search_fields = (
        'status', 'title', 'story', 'pitch',
        'place.locality', 'place.postal_code', 'place.formatted_address',
        'theme.name', 'owner.full_name', 'promoter.full_name',
        'activities.office_location.name', 'activities.office_location.city',
    )

    boost = {'title': 2}

    def get_default_filters(self, request):
        fields = super(InitiativeSearchFilter, self).get_filter_fields(request)

        permission = 'initiatives.api_read_initiative'

        if not request.user.has_perm(permission):
            filters = [Term(owner_id=request.user.id)]

            if 'owner.id' not in fields:
                filters.append(Term(status='approved'))

            return filters
        elif 'owner.id' in fields and request.user.is_authenticated:
            value = request.user.pk
            return [
                Nested(path='owner', query=Term(owner__id=value)) |
                Nested(path='promoter', query=Term(promoter__id=value)) |
                Nested(path='activity_managers', query=Term(activity_managers__id=value)) |
                Nested(path='activity_owners', query=Term(activity_owners__id=value)) |
                Term(status='approved')
            ]
        else:
            return [Term(status='approved')]

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
