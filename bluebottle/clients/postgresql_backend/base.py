from tenant_schemas.postgresql_backend import base


class DatabaseWrapper(base.DatabaseWrapper):
    pass


DatabaseError = base.DatabaseError
IntegrityError = base.IntegrityError
