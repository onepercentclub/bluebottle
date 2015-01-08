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
        MULTITENANT_DIR/greatbarier/static/images/logo.jpg

        """
        matches = []
        tenants = Client.objects.all()
        tenant_dir = getattr(settings, 'MULTI_TENANT_DIR', None)
        if not tenant_dir:
            return matches

        for tenant in tenants:
            if "{0}/".format(tenant.client_name) in path:
                tenant_path = path.replace('{0}/'.format(tenant.client_name),
                                           '{0}/static/'.format(tenant.client_name))
                print tenant_path
                local_path = safe_join(tenant_dir, tenant_path)
                print local_path
                if os.path.exists(local_path):
                    return local_path
        return
