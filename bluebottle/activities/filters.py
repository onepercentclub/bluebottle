from elasticsearch_dsl.query import FunctionScore, SF, Terms
from bluebottle.utils.filters import ElasticSearchFilter
from bluebottle.activities.documents import ActivityDocument


class ActivitySearchFilter(ElasticSearchFilter):
    document = ActivityDocument

    sort_fields = {
        'date': ('-created', ),
        'alphabetical': ('title_keyword', ),
        'popularity': 'popularity',
    }
    filters = (
        'owner.id',
        'theme.id',
        'country',
        'categories.slug',
        'expertise.id',
        'type',
        'status',
    )

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
                    missing=0
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

    def get_default_filters(self, request):
        return [Terms(review_status=['approved'])]
