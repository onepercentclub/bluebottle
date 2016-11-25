from django.test.runner import DiscoverRunner
from django.db import connection, IntegrityError
from django.core import management

from tenant_schemas.utils import get_tenant_model

from bluebottle.test.factory_models.rates import RateSourceFactory, RateFactory
from bluebottle.test.utils import InitProjectDataMixin


class MultiTenantRunner(DiscoverRunner, InitProjectDataMixin):
    def setup_databases(self, *args, **kwargs):
        parallel = self.parallel
        self.parallel = 0
        result = super(MultiTenantRunner, self).setup_databases(**kwargs)
        self.parallel = parallel

        connection.set_schema_to_public()

        tenant2, _created = get_tenant_model().objects.get_or_create(
            domain_url='testserver2',
            schema_name='test2',
            client_name='test2')

        tenant, _created = get_tenant_model().objects.get_or_create(
            domain_url='testserver',
            schema_name='test',
            client_name='test')

        connection.set_tenant(tenant)

        self.init_projects()


        if parallel > 1:
            for index in range(parallel):
                connection.creation.clone_test_db(
                    number=index + 1,
                    verbosity=self.verbosity,
                    keepdb=self.keepdb,
                )

        try:
            rate_source = RateSourceFactory.create(base_currency='USD')
            RateFactory.create(source=rate_source, currency='USD', value=1)
            RateFactory.create(source=rate_source, currency='EUR', value=1.5)
            RateFactory.create(source=rate_source, currency='XOF', value=1000)
            RateFactory.create(source=rate_source, currency='NGN', value=500)
        except IntegrityError:
            pass

        return result
