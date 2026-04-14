import locale
import os
from builtins import range

from django.conf import settings
from django.core.management import call_command
from django.db import IntegrityError, connection
from django.test import runner as django_test_runner
from django.test.runner import ParallelTestSuite
from django_slowtests.testrunner import DiscoverSlowestTestsRunner
from djmoney.contrib.exchange.models import ExchangeBackend, Rate
from tenant_schemas.utils import get_tenant_model

from bluebottle.clients.utils import LocalTenant
from bluebottle.test.utils import InitProjectDataMixin


def _wait_for_es_indices():
    """Wait for Elasticsearch indices to be ready for search (refresh)."""
    try:
        from elasticsearch_dsl import connections
        conn = connections.get_connection()
        conn.indices.refresh(index="*")
    except Exception:
        pass


def _wipe_stale_pid_test_elasticsearch_indices():
    """
    Delete indices matching {ELASTICSEARCH_TEST_INDEX_PREFIX}-pid* (orphaned
    single-process test runs). Prevents hitting cluster.max_shards_per_node
    after many local/IDE test runs. Does not delete test-w* (parallel workers).
    """
    if not getattr(settings, 'ELASTICSEARCH_TEST_WIPE_STALE_PID_INDICES', False):
        return
    prefix = getattr(settings, 'ELASTICSEARCH_TEST_INDEX_PREFIX', None)
    if not prefix:
        return
    try:
        from elasticsearch_dsl import connections
        es = connections.get_connection()
        pattern = f'{prefix}-pid*'
        es.indices.delete(
            index=pattern,
            params={'ignore_unavailable': 'true'},
        )
    except Exception:
        pass


def _setup_es_indices():
    """
    Create Elasticsearch indices for all tenants. Does not return until indices
    are set up (and refreshed). Tests must not run until this completes.
    """
    _wipe_stale_pid_test_elasticsearch_indices()
    Tenant = get_tenant_model()
    for tenant in Tenant.objects.exclude(schema_name='public'):
        with LocalTenant(tenant):
            call_command("search_index", "--delete", "-f", verbosity=0)
            call_command("search_index", "--create", verbosity=0)
            _wait_for_es_indices()


def _init_worker_with_es(
    counter,
    initial_settings=None,
    serialized_contents=None,
    process_setup=None,
    process_setup_args=None,
    debug_mode=None,
):
    with counter.get_lock():
        counter.value += 1
        worker_id = counter.value

    try:
        max_workers = int(os.environ.get("DJANGO_TEST_WORKERS", "0") or 0)
    except ValueError:
        max_workers = 0

    if max_workers > 0:
        worker_id = ((worker_id - 1) % max_workers) + 1

    django_test_runner._worker_id = worker_id

    start_method = django_test_runner.multiprocessing.get_start_method()
    if start_method == "spawn":
        if process_setup and callable(process_setup):
            if process_setup_args is None:
                process_setup_args = ()
            process_setup(*process_setup_args)
        django_test_runner.django.setup()
        django_test_runner.setup_test_environment(debug=debug_mode)

    for alias in django_test_runner.connections:
        connection = django_test_runner.connections[alias]
        if start_method == "spawn":
            connection.settings_dict.update(initial_settings[alias])
            if serialized_contents and serialized_contents.get(alias):
                connection._test_serialized_contents = serialized_contents[alias]
        connection.creation.setup_worker_connection(worker_id)

    if worker_id:
        os.environ["DJANGO_TEST_PROCESS_NUMBER"] = str(worker_id)
    # Complete ES index setup before this worker is used; Django does not
    # assign tests to a worker until its initializer returns.
    _setup_es_indices()


class ParallelTestSuiteWithES(ParallelTestSuite):
    """Parallel suite that sets up Elasticsearch indices in each worker before any tests run."""
    init_worker = _init_worker_with_es


class MultiTenantRunner(DiscoverSlowestTestsRunner, InitProjectDataMixin):
    parallel_test_suite = ParallelTestSuiteWithES

    def setup_databases(self, *args, **kwargs):
        self.keepdb = getattr(settings, 'KEEPDB', self.keepdb)
        parallel = self.parallel
        if parallel:
            os.environ["DJANGO_TEST_WORKERS"] = str(parallel)
        self.parallel = 0
        result = super(MultiTenantRunner, self).setup_databases(**kwargs)
        self.parallel = parallel
        # Set local explicitely so test also run on OSX
        locale.setlocale(locale.LC_ALL, 'en_GB.UTF-8')

        connection.set_schema_to_public()

        tenant2, _created = get_tenant_model().objects.get_or_create(
            domain_url="test2.localhost",
            name="Test Too",
            schema_name="test2",
            client_name="test2",
        )

        connection.set_tenant(tenant2)
        self.init_projects()

        connection.set_schema_to_public()

        tenant, _created = get_tenant_model().objects.get_or_create(
            domain_url="test.localhost",
            name="Test",
            schema_name="test",
            client_name="test",
        )

        connection.set_tenant(tenant)
        self.init_projects()

        try:
            backend, _created = ExchangeBackend.objects.get_or_create(
                base_currency='USD',
                name='openexchangerates.org'
            )
            Rate.objects.update_or_create(backend=backend, currency='USD', defaults={'value': 1})
            Rate.objects.update_or_create(backend=backend, currency='EUR', defaults={'value': 1.5})
            Rate.objects.update_or_create(backend=backend, currency='XOF', defaults={'value': 1000})
            Rate.objects.update_or_create(backend=backend, currency='NGN', defaults={'value': 500})
            Rate.objects.update_or_create(backend=backend, currency='UGX', defaults={'value': 5000})
            Rate.objects.update_or_create(backend=backend, currency='KES', defaults={'value': 100})
        except IntegrityError:
            pass

        # Single process: set up ES indices before returning so no tests run until they are ready.
        if parallel <= 1:
            _setup_es_indices()

        if parallel > 1:
            for index in range(parallel):
                connection.creation.clone_test_db(
                    suffix=index + 1,
                    verbosity=self.verbosity,
                    keepdb=self.keepdb,
                )

        return result

    def run_checks(self, *args, **kwargs):
        return
