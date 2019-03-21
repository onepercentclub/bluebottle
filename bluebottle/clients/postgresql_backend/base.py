from tenant_schemas.postgresql_backend import base

from bluebottle.clients import properties


class DatabaseWrapper(base.DatabaseWrapper):
    def set_tenant(self, tenant, *args, **kwargs):
        """
        Main API method to current database schema,
        but it does not actually modify the db connection.
        """
        super(DatabaseWrapper, self).set_tenant(tenant, *args, **kwargs)

        properties.set_tenant(tenant)
