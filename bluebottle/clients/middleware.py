from future import standard_library
standard_library.install_aliases()
from django.utils.deprecation import MiddlewareMixin
from urllib.parse import urljoin

from django.db import connection
from django.conf import settings
from django.shortcuts import redirect


class MediaMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if (
            response.status_code == 404 and
            request.path.startswith(settings.MEDIA_URL) and
            connection.tenant.schema_name not in request.path
        ):
            return redirect(
                request.path.replace(settings.MEDIA_URL,
                                     urljoin(settings.MEDIA_URL, connection.tenant.schema_name + '/'))
            )

        return response
