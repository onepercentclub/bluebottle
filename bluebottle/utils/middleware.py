from importlib import import_module

from django import http
from django.conf.urls.i18n import is_language_prefix_patterns_used
from django.middleware.locale import LocaleMiddleware
from django.conf import settings
from django.contrib.sessions import middleware
from django.db import connection
from django.utils import translation

from tenant_extras.middleware import tenant_translation
from tenant_extras.utils import get_tenant_properties

from bluebottle.utils.models import get_languages, get_default_language


class SubDomainSessionMiddleware(middleware.SessionMiddleware):
    def process_request(self, request):
        engine = import_module(settings.SESSION_ENGINE)
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
        if session_key is None:
            # Look for old cookie in request for auth purposes.
            session_key = request.COOKIES.get('sessionid', None)

        request.session = engine.SessionStore(session_key)


class APILanguageMiddleware(middleware.SessionMiddleware):
    def process_request(self, request):
        if request.path.startswith('/api'):
            try:
                language = request.META['HTTP_X_APPLICATION_LANGUAGE']
                if language not in [lang.full_code for lang in get_languages()]:
                    language = get_default_language()
            except KeyError:
                language = get_default_language()

            translation.activate(language)

            translation._trans._active.value = tenant_translation(
                language, connection.tenant.client_name
            )
            request.LANGUAGE_CODE = translation.get_language()


class TenantLocaleMiddleware(LocaleMiddleware):
    def process_response(self, request, response):
        """
        Redirect to default tenant language if none is set.
        """
        if response.status_code in [301, 302]:
            # No need to check for a locale redirect if the response is already a redirect.
            return response

        ignore_paths = getattr(settings, 'LOCALE_REDIRECT_IGNORE', None)

        # Get language from path
        urlconf = getattr(request, 'urlconf', settings.ROOT_URLCONF)
        if is_language_prefix_patterns_used(urlconf):
            language_from_path = translation.get_language_from_path(
                request.path_info
            )
            # If ignore paths or language set, then just pass the response
            if language_from_path or (ignore_paths and request.path.startswith(ignore_paths)):
                return response

        # Redirect to default tenant language
        lang_code = getattr(get_tenant_properties(), 'LANGUAGE_CODE', None)
        new_location = '/{0}{1}'.format(lang_code, request.get_full_path())

        return http.HttpResponseRedirect(new_location)
