from bluebottle.initiatives.documents import InitiativeDocument, initiative
from bluebottle.initiatives.models import InitiativePlatformSettings

from bluebottle.segments.models import SegmentType
from bluebottle.utils.filters import (
    ElasticSearchFilter, Search, TranslatedFacet, NamedNestedFacet,
    SegmentFacet
)


class InitiativeSearch(Search):
    doc_types = [InitiativeDocument]

    fields = [
        (None, ('title^3', 'story^2', 'pitch')),
        ('owner', ('full_name', 'full_name')),
    ]

    facets = {}

    possible_facets = {
        'theme': TranslatedFacet('theme'),
        'category': TranslatedFacet('categories', 'title'),
        'country': NamedNestedFacet('country'),
        'location': NamedNestedFacet('office'),
    }

    def __new__(cls, search, filter):
        settings = InitiativePlatformSettings.objects.get()
        result = super().__new__(cls, settings.activity_search_filters)

        for segment_type in SegmentType.objects.all():
            result.facets[f'segment.{segment_type.slug}'] = SegmentFacet(segment_type)

        return result


class InitiativeSearchFilter(ElasticSearchFilter):
    index = initiative
    search_class = InitiativeSearch
