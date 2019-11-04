from urlparse import urljoin

from django.db import connection
from django.conf import settings
from django.shortcuts import redirect


class MediaMiddleware(object):
    def process_response(self, request, response):
        if (
            response.status_code == 404 and
            request.path.startswith(settings.MEDIA_URL) and
            connection.tenant.client_name not in request.path
        ):
            return redirect(
                request.path.replace(settings.MEDIA_URL,
                                     urljoin(settings.MEDIA_URL, connection.tenant.schema_name + '/'))
            )

        return response
