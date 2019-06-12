import os

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from tenant_schemas.storage import TenantFileSystemStorage

__all__ = ('TenantFileSystemStorage',)


class TenantFileSystemStorage(TenantFileSystemStorage):
    """
    Lookup files first in $TENANT_BASE//media/ then in default location
    """

    def path(self, name):
        from django.db import connection
        from django.utils._os import safe_join
        # FIXME: These imports are inline so that the connection object
        # can be mocked in tests

        if connection.tenant:
            location = safe_join(settings.TENANT_BASE,
                                 connection.tenant.schema_name)
        else:
            location = self.location
        try:
            path = safe_join(location, name)
        except ValueError:
            raise SuspiciousFileOperation(
                "Attempted access to '%s' denied." % name)
        return os.path.normpath(path)
