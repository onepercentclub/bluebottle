import os

from django.core.exceptions import SuspiciousFileOperation
from tenant_schemas.storage import TenantFileSystemStorage as BaseTenantFileSystemStorage

from django.utils._os import safe_join
from django.db import connection

__all__ = ('TenantFileSystemStorage',)


class TenantFileSystemStorage(BaseTenantFileSystemStorage):
    """
    Lookup files first in $TENANT_BASE//media/ then in default location
    """

    def path(self, name):
        location = self.location
        try:
            path = safe_join(location, name)
        except ValueError:
            raise SuspiciousFileOperation(
                "Attempted access to '%s' denied." % name)
        return os.path.normpath(path)

    @property
    def location(self):
        if connection.tenant:
            return os.path.abspath(safe_join(self.base_location, connection.tenant.schema_name))
        else:
            return super().location
