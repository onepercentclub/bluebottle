from django.utils._os import safe_join
import os
from django.conf import settings
from django.contrib.staticfiles.finders import FileSystemFinder
from bluebottle.clients.models import Client


class TenantStaticFilesFinder(FileSystemFinder):
    def find(self, path, all=False):
        """
        Looks for files in the client static directories.
        static/assets/greatbarier/images/logo.jpg
        will translate to
        MULTI_TENANT_DIR/greatbarier/static/images/logo.jpg

        """
        tenants = Client.objects.all()
        tenant_dir = getattr(settings, 'MULTI_TENANT_DIR', None)

        if not tenant_dir:
            return []

        for tenant in tenants:
            if "{0}/".format(tenant.client_name) in path:
                tenant_path = path.replace('{0}/'.format(tenant.client_name),
                                           '{0}/static/'.format(
                                               tenant.client_name))
                local_path = safe_join(tenant_dir, tenant_path)
                if os.path.exists(local_path):
                    if all:
                        return [local_path]
                    return local_path
        return []
