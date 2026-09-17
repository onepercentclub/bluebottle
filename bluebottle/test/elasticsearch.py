from django.conf import settings
from django.test.utils import override_settings
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl.connections import connections

from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


def _index_names():
    prefix = getattr(settings, 'ELASTICSEARCH_TEST_INDEX_PREFIX', None)
    names = []
    for index in registry.get_indices():
        name = index._name
        if not name:
            continue
        if prefix and not name.startswith(prefix + '-'):
            continue
        names.append(name)
    return names


def refresh_search_indices():
    names = _index_names()
    if not names:
        return
    connections.get_connection().indices.refresh(index=','.join(names))


def clear_search_indices():
    names = _index_names()
    if not names:
        return
    connections.get_connection().delete_by_query(
        index=','.join(names),
        body={'query': {'match_all': {}}},
        refresh=True,
        conflicts='proceed',
        ignore=[404],
        ignore_unavailable=True,
    )


def ensure_search_indices():
    for index in registry.get_indices():
        if not index.exists():
            index.create()


class SearchJSONAPITestClient(JSONAPITestClient):
    def request(self, **kwargs):
        refresh_search_indices()
        return super().request(**kwargs)


@override_settings(
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=False,
)
class ElasticsearchTestCase(BluebottleTestCase):
    """
    Elasticsearch tests that reuse the runner's indices.

    django_elasticsearch_dsl's ESTestCase deletes and recreates every index
    on each test. Document.django.auto_refresh is also fixed at import time,
    so AUTO_REFRESH settings overrides do not disable per-write waits.
    """

    @classmethod
    def setUpClass(cls):
        super(ElasticsearchTestCase, cls).setUpClass()
        cls._auto_refresh_restore = [
            (doc, doc.django.auto_refresh)
            for doc in registry.get_documents()
        ]
        for doc, _value in cls._auto_refresh_restore:
            doc.django.auto_refresh = False
        ensure_search_indices()

    @classmethod
    def tearDownClass(cls):
        for doc, value in getattr(cls, '_auto_refresh_restore', []):
            doc.django.auto_refresh = value
        super(ElasticsearchTestCase, cls).tearDownClass()

    def setUp(self):
        super(ElasticsearchTestCase, self).setUp()
        clear_search_indices()
        self.client = SearchJSONAPITestClient()
