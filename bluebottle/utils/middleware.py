from importlib import import_module

from django.conf import settings
from django.contrib.sessions import middleware
from django.db import connection
from django.utils import translation

from tenant_extras.middleware import tenant_translation

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
                if language not in [lang.code for lang in get_languages()]:
                    language = get_default_language()
            except KeyError:
                language = get_default_language()

            translation.activate(language)

            translation._trans._active.value = tenant_translation(
                language, connection.tenant.client_name
            )
            request.LANGUAGE_CODE = translation.get_language()
