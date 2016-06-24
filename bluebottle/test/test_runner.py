from django.test.runner import DiscoverRunner
from django.db import connection

from tenant_schemas.utils import get_tenant_model

from bluebottle.test.utils import InitProjectDataMixin


class MultiTenantRunner(DiscoverRunner, InitProjectDataMixin):
    def setup_databases(self, *args, **kwargs):
        result = super(MultiTenantRunner, self).setup_databases(*args, **kwargs)

        # Create secondary tenant
        connection.set_schema_to_public()
        tenant_domain = 'testserver2'
        tenant2 = get_tenant_model()(
            domain_url=tenant_domain,
            schema_name='test2',
            client_name='test2')

        tenant2.save(
            verbosity=self.verbosity)

        # Add basic data for tenant
        connection.set_tenant(tenant2)
        self.init_projects()

        # Create main tenant
        connection.set_schema_to_public()
        tenant_domain = 'testserver'
        tenant = get_tenant_model()(
            domain_url=tenant_domain,
            schema_name='test',
            client_name='test')

        tenant.save(
            verbosity=self.verbosity)

        connection.set_tenant(tenant)

        return result
