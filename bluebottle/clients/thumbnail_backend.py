from sorl.thumbnail.base import ThumbnailBackend
from django.db import connection

class TenantThumbnailBackend(ThumbnailBackend):
    """ Make sure the tenant client_name is used when generating cache key """
    def _get_thumbnail_filename(self, source, geometry_string, options):
        options = options.copy()
        try:
            options['tenant'] = connection.tenant.client_name
        except AttributeError:
            pass

        return super(TenantThumbnailBackend, self
                     )._get_thumbnail_filename(source, geometry_string, options)
