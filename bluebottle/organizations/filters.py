import logging

from bluebottle.organizations.documents import organization
from bluebottle.utils.filters import (
    ElasticSearchFilter,
    Search,
)

logger = logging.getLogger(__name__)


class OrganizationSearch(Search):
    doc_types = [organization]

    sorting = {
        "created": ["created"],
        "-created": ["-created"],
    }
    default_sort = "-created"

    fields = [
        (None, ("name^3", "slogan^2", "story^1")),
    ]

    facets = {}
    possible_facets = {}


class OrganizationSearchFilter(ElasticSearchFilter):
    index = organization
    search_class = OrganizationSearch
