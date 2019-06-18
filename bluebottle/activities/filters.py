from elasticsearch_dsl.query import FunctionScore, SF
from bluebottle.utils.filters import ElasticSearchFilter
from bluebottle.activities.documents import ActivityDocument


class ActivitySearchFilter(ElasticSearchFilter):
    document = ActivityDocument

    sort_fields = {
        'date': ('-created', ),
        'alphabetical': ('title', ),
        'popularity': 'popularity',
    }

    filters = ('owner.id', )
    search_fields = (
        'status', 'title', 'description', 'owner.name',
    )

    boost = {'title': 2}

    def get_sort_popularity(self):
        return FunctionScore(
            score_mode='multiply',
            functions=[
                SF(
                    'field_value_factor',
                    field='contribution_count',
                ),
                SF(
                    'gauss',
                    multi_value_mode="avg",
                    contributions={
                        'origin': 'now',
                        'scale': '5d',
                        'offset': 0,
                    },
                ),
            ]
        )
