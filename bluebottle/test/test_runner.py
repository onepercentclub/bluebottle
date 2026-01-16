import locale
import os
from builtins import range

from django.conf import settings
from django.core.management import call_command
from django.db import IntegrityError, connection
from django_slowtests.testrunner import DiscoverSlowestTestsRunner
from djmoney.contrib.exchange.models import ExchangeBackend, Rate
from tenant_schemas.utils import get_tenant_model

from bluebottle.test.utils import InitProjectDataMixin

# Use process-specific flags to allow parallel test execution
_ES_READY = {}

class MultiTenantRunner(DiscoverSlowestTestsRunner, InitProjectDataMixin):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)

        # Use process ID to allow each parallel test process to create its own indices
        process_id = os.getpid()
        if _ES_READY.get(process_id, False):
            return

        # Make sure each worker has a stable prefix (you already do this)
        # settings.ELASTICSEARCH_TEST_INDEX_PREFIX = ...

        # 2) Always clean ES for this worker prefix, then create indices
        # Fast + avoids alias rebuild collisions
        # Each process needs to create its own indices with process-specific names
        call_command("search_index", "--delete", "-f", verbosity=0)
        call_command("search_index", "--create", verbosity=0)

        # Only if you really need a full reindex from DB:
        # call_command("search_index", "--rebuild", "--use-alias", verbosity=0)

        _ES_READY[process_id] = True

    def setup_databases(self, *args, **kwargs):
        self.keepdb = getattr(settings, 'KEEPDB', self.keepdb)
        parallel = self.parallel
        self.parallel = 0
        result = super(MultiTenantRunner, self).setup_databases(**kwargs)
        self.parallel = parallel
        # Set local explicitly so test also run on OSX
        locale.setlocale(locale.LC_ALL, 'en_GB.UTF-8')

        connection.set_schema_to_public()

        tenant2, _created = get_tenant_model().objects.get_or_create(
            domain_url='testserver2',
            name='Test Too',
            schema_name='test2',
            client_name='test2')

        connection.set_tenant(tenant2)
        self.init_projects()

        connection.set_schema_to_public()

        tenant, _created = get_tenant_model().objects.get_or_create(
            domain_url='testserver',
            name='Test',
            schema_name='test',
            client_name='test')

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
