from django.conf import settings
from django.test.runner import ParallelTestSuite
from django_elasticsearch_dsl.registries import registry
from django_slowtests.testrunner import DiscoverSlowestTestsRunner
from elasticsearch_dsl.connections import connections

_worker_id = 0


def _elastic_search_init_worker(counter):
    global _worker_id

    with counter.get_lock():
        counter.value += 1
        _worker_id = counter.value

    for alias in connections:
        connection = connections[alias]
        settings_dict = connection.creation.get_test_db_clone_settings(_worker_id)
        connection.settings_dict.update(settings_dict)
        connection.close()

    worker_connection_postfix = f"_worker_{_worker_id}"
    for alias in connections:
        connections.configure(**{alias + worker_connection_postfix: settings.ELASTICSEARCH_DSL["default"]})

    for doc in registry.get_documents():
        doc._doc_type.index += f"_{_worker_id}"
        doc._doc_type._using = doc.doc_type._using + worker_connection_postfix

    for index in registry.get_indices():
        index._name += f"_{_worker_id}"
        index._using = doc.doc_type._using + worker_connection_postfix
        index.delete(ignore=[404])
        index.create()


class ElasticParallelTestSuite(ParallelTestSuite):
    init_worker = _elastic_search_init_worker


class MultiTenantRunner(DiscoverSlowestTestsRunner):
    parallel_test_suite = ElasticParallelTestSuite
