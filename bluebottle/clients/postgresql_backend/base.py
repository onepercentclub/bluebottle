from tenant_schemas.postgresql_backend import base

from bluebottle.clients import properties

from tenant_schemas.postgresql_backend.introspection import DatabaseSchemaIntrospection as TenantDatabaseSchemaIntrospection


class DatabaseSchemaIntrospection(TenantDatabaseSchemaIntrospection):
    def get_sequences(self, cursor, table_name, table_fields=()):
        cursor.execute(
            """
            SELECT
                s.relname AS sequence_name,
                a.attname AS colname
            FROM
                pg_class s
                JOIN pg_depend d ON d.objid = s.oid
                    AND d.classid = 'pg_class'::regclass
                    AND d.refclassid = 'pg_class'::regclass
                JOIN pg_attribute a ON d.refobjid = a.attrelid
                    AND d.refobjsubid = a.attnum
                JOIN pg_class tbl ON tbl.oid = d.refobjid
                    AND tbl.relname = %s
                    AND pg_catalog.pg_table_is_visible(tbl.oid)
            WHERE
                s.relkind = 'S';
        """,
            [table_name],
        )
        return [
            {"name": row[0], "table": table_name, "column": row[1]}
            for row in cursor.fetchall()
        ]

class DatabaseWrapper(base.DatabaseWrapper):
    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.introspection = DatabaseSchemaIntrospection(self)
        self.set_schema_to_public()

    def set_tenant(self, tenant, *args, **kwargs):
        """
        Main API method to current database schema,
        but it does not actually modify the db connection.
        """
        super(DatabaseWrapper, self).set_tenant(tenant, *args, **kwargs)

        properties.set_tenant(tenant)
