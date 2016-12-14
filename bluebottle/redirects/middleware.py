from __future__ import unicode_literals

import regex

from django import http
from django.conf import settings
from django.db import connection

from bluebottle.redirects.models import Redirect
from bluebottle.clients import properties


class RedirectFallbackMiddleware(object):
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

        language = properties.LANGUAGE_CODE

        t = getattr(_active, "value", None)
        if t is not None:
            try:
                lan = t.to_language()
                if [i[0] for i in properties.LANGUAGES if i[0] == lan]:
                    language = lan
            except AttributeError:
                pass

        def redirect_target(new_path):
            if new_path.startswith("http:") or new_path.startswith("https:"):
                return new_path
            return http_host + '/' + language + new_path

        redirects = Redirect.objects.all().order_by('fallback_redirect')
        for redirect in redirects:
            # Attempt a regular match
            if redirect.old_path == full_path:
                redirect.nr_times_visited += 1
                redirect.save()
                return http.HttpResponsePermanentRedirect(
                    redirect_target(redirect.new_path))

            if settings.APPEND_SLASH and not request.path.endswith('/'):
                # Try appending a trailing slash.
                path_len = len(request.path)
                slashed_full_path = full_path[:path_len] + '/' + full_path[path_len:]

                if redirect.old_path == slashed_full_path:
                    redirect.nr_times_visited += 1
                    redirect.save()
                    return http.HttpResponsePermanentRedirect(
                        redirect_target(redirect.new_path))

        # Attempt all regular expression redirects
        reg_redirects = Redirect.objects.filter(
            regular_expression=True).order_by('fallback_redirect')
        for redirect in reg_redirects:
            try:
                old_path = regex.compile(redirect.old_path, regex.IGNORECASE)
            except regex.error:
                # old_path does not compile into regex,
                # ignore it and move on to the next one
                continue

            if regex.match(redirect.old_path, full_path):
                # Convert $1 into \1 (otherwise users would have
                # to enter \1 via the admin which would have to be escaped)
                new_path = redirect.new_path.replace('$', '\\')
                replaced_path = regex.sub(old_path, new_path, full_path)
                redirect.nr_times_visited += 1
                redirect.save()
                return http.HttpResponsePermanentRedirect(
                    redirect_target(replaced_path))

        # No redirect was found. Return the response.
        return response
