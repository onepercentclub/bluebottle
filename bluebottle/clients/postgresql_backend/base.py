from tenant_schemas.postgresql_backend.base import DatabaseWrapper as TenantDatabaseWrapper

from bluebottle.clients import properties


class DatabaseWrapper(TenantDatabaseWrapper):
    def set_tenant(self, tenant, *args, **kwargs):
        """
        Main API method to current database schema,
        but it does not actually modify the db connection.
        """
        super(DatabaseWrapper, self).set_tenant(tenant, *args, **kwargs)

        properties.set_tenant(tenant)
