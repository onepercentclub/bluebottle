from django.test.runner import DiscoverRunner
from django.db import connection

from tenant_schemas.utils import get_tenant_model


class MultiTenantRunner(DiscoverRunner):
    def setup_databases(self, *args, **kwargs):
        result = super(MultiTenantRunner, self).setup_databases(*args, **kwargs)
        tenant_domain = 'testserver'
        tenant = get_tenant_model()(
            domain_url=tenant_domain,
            schema_name='test',
            client_name='test')

        tenant.save(
            verbosity=self.verbosity)

        connection.set_tenant(tenant)

        return result



