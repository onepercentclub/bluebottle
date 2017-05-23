from django.contrib.sessions import middleware
from django.conf import settings
from django.utils import translation
from importlib import import_module

from bluebottle.clients import properties


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
                if language not in [lang[0] for lang in properties.LANGUAGES]:
                    language = properties.LANGUAGE_CODE
            except KeyError:
                language = properties.LANGUAGE_CODE

            translation.activate(language)
