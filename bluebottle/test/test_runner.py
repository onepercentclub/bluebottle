import locale
from builtins import range

from django.db import connection, IntegrityError
from django_slowtests.testrunner import DiscoverSlowestTestsRunner
from djmoney.contrib.exchange.models import Rate, ExchangeBackend
from tenant_schemas.utils import get_tenant_model

from bluebottle.test.utils import InitProjectDataMixin


class MultiTenantRunner(DiscoverSlowestTestsRunner, InitProjectDataMixin):
    def setup_databases(self, *args, **kwargs):

        parallel = self.parallel
        self.parallel = 0
        result = super(MultiTenantRunner, self).setup_databases(**kwargs)
        self.parallel = parallel
        # Set local explicitely so test also run on OSX
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
            backend, _created = ExchangeBackend.objects.get_or_create(base_currency='USD')
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
                    number=index + 1,
                    verbosity=self.verbosity,
                    keepdb=self.keepdb,
                )

        return result
