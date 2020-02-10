import locale

from django.db import connection, IntegrityError
from django_slowtests.testrunner import DiscoverSlowestTestsRunner

from tenant_schemas.utils import get_tenant_model

from bluebottle.test.factory_models.rates import RateSourceFactory, RateFactory
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
            rate_source = RateSourceFactory.create(base_currency='USD')
            RateFactory.create(source=rate_source, currency='USD', value=1)
            RateFactory.create(source=rate_source, currency='EUR', value=1.5)
            RateFactory.create(source=rate_source, currency='XOF', value=1000)
            RateFactory.create(source=rate_source, currency='NGN', value=500)
            RateFactory.create(source=rate_source, currency='UGX', value=5000)
            RateFactory.create(source=rate_source, currency='KES', value=100)
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
