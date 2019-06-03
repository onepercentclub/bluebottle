from bluebottle.utils.filters import ElasticSearchFilter
from bluebottle.activities.documents import ActivityDocument


class ActivitySearchFilter(ElasticSearchFilter):
    document = ActivityDocument

    sort_fields = {
        'date': ('-created', ),
        'alphabetical': ('title', ),
    }

    filters = ('owner.id', )
    search_fields = (
        'status', 'title', 'description', 'owner.name',
    )

    boost = {'title': 2}
