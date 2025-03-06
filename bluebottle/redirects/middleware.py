from __future__ import unicode_literals

from django import http
from django.conf import settings
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

from bluebottle.redirects.models import Redirect
from bluebottle.utils.models import get_default_language, get_languages


class RedirectFallbackMiddleware(MiddlewareMixin):
    """
    A modified version of django.contrib.redirects, this app allows
    us to optionally redirect users using regular expressions.

    It is based on: http://djangosnippets.org/snippets/2784/
    """

    def process_response(self, request, response):
        if response.status_code != 404:
            # No need to check for a redirect for non-404 responses.
            return response

        if connection.tenant.schema_name == 'public':
            # No tenant selected
            return response

        full_path = request.get_full_path()
        http_host = request.META.get('HTTP_HOST', '')

        if http_host:
            # Crappy workaround for localhost.
            # Always default to https if not on local machine.
            # This will hopefully fix Safari problems.

            if http_host in ['testserver', 'localhost', 'localhost:8000',
                             'localhost:8081',
                             '127.0.0.1:8000', '127.0.0.1'] or \
                    http_host.split(":", 1)[0].endswith("localhost"):
                http_host = 'http://' + http_host
            else:
                http_host = 'https://' + http_host

        # Get the language that's active in the current thread if
        # its also in our 'allowed' languages propertie in settings
        # If there's no language, fallback to the LANGUAGE_CODE
        from django.utils.translation.trans_real import _active

        language = get_default_language()

        t = getattr(_active, "value", None)
        if t is not None:
            try:
                lan = t.to_language()
                if lan in [lang.code for lang in get_languages()]:
                    language = lan
            except AttributeError:
                pass

        def redirect_target(new_path):
            if new_path.startswith("http:") or new_path.startswith("https:"):
                return new_path
            return http_host + '/' + language + new_path

        redirects = Redirect.objects.all()
        for redirect in redirects:
            # Attempt a regular match
            if redirect.old_path == full_path:
                return http.HttpResponsePermanentRedirect(
                    redirect_target(redirect.new_path))

            if settings.APPEND_SLASH and not request.path.endswith('/'):
                # Try appending a trailing slash.
                path_len = len(request.path)
                slashed_full_path = full_path[:path_len] + '/' + full_path[path_len:]

                if redirect.old_path == slashed_full_path:
                    return http.HttpResponsePermanentRedirect(
                        redirect_target(redirect.new_path))

        # No redirect was found. Return the response.
        return response
