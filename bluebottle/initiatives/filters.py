from elasticsearch_dsl import Q
from elasticsearch_dsl.query import Term, Nested

from bluebottle.utils.filters import ElasticSearchFilter
from bluebottle.initiatives.documents import InitiativeDocument


class InitiativeSearchFilter(ElasticSearchFilter):
    document = InitiativeDocument

    sort_fields = {
        'date': ('-created', ),
        'alphabetical': ('title_keyword', ),
    }
    default_sort_field = 'date'

    filters = (
        'owner.id', 'activity_manager.id',
        'theme.id', 'place.country',
        'categories.id', 'categories.slug',
    )

    search_fields = (
        'status', 'title', 'story', 'pitch',
        'place.locality', 'place.postal_code',
        'theme.name', 'owner.full_name', 'promoter.full_name',
    )

    boost = {'title': 2}

    def get_default_filters(self, request):
        fields = super(InitiativeSearchFilter, self).get_filter_fields(request)

        permission = 'initiatives.api_read_initiative'
        if not request.user.has_perm(permission):
            return [Term(owner_id=request.user.id), Term(status='approved')]
        elif 'owner.id' in fields:
            return [
                Term(owner_id=request.user.id) |
                Term(activity_manager_id=request.user.id) |
                Term(promoter_id=request.user.id) |
                Term(status='approved')
            ]
        else:
            return [Term(status='approved')]

    def get_filter(self, request, field):
        # Also return activity_manger.id when filtering on owner.id
        if field == 'owner.id':
            value = request.GET['filter[{}]'.format(field)]
            return Q(
                Nested(path='owner', query=Term(**{field: value})) |
                Nested(path='promoter', query=Term(promoter__id=value)) |
                Nested(path='activity_manager', query=Term(activity_manager__id=value))
            )

        return super(InitiativeSearchFilter, self).get_filter(request, field)
