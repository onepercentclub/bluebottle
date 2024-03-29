from past.builtins import execfile
import logging
from threading import local

from django.conf import settings
from django.utils._os import safe_join


logger = logging.getLogger(__name__)


class TenantProperties(local):
    """
    A tenant property file is read from the MULTI_TENANT_DIR/<tenant_name>/properties.py.
    It can contain arbitrary python expressions and a reference to 'settings' will be available.
    """
    tenant_properties = {}

    def set_tenant(self, tenant):
        self.tenant = tenant
        self.tenant_properties = {}

        # Always default to standard django settings, e.g.
        # when tenant has no specific config, has no directory
        # or when no MULTI_TENANT_DIR is configured

        from tenant_schemas.postgresql_backend.base import FakeTenant
        try:
            props_mod = safe_join(settings.MULTI_TENANT_DIR,
                                  tenant.client_name,
                                  "settings.py")
            # try to load tenant specific properties. We're using execfile since tenant
            # directories are not python packages (e.g. no __init__.py)
            execfile(props_mod, dict(settings=settings),
                     self.tenant_properties)

        except (ImportError, AttributeError, IOError):
            if not isinstance(tenant, FakeTenant):
                logger.debug('No tenant properties found for: {0}'.format(tenant.client_name))

            pass

    def __getattr__(self, k):
        """
        Search (in that specific order) tenant properties and settings.
        Raise AttributeError if not found.
        """
        try:
            return self.tenant_properties[k]
        except (AttributeError, KeyError):
            # May raise AttributeError which is the behaviour we expect
            return getattr(settings, k)


properties = TenantProperties()
