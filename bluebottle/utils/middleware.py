from django.contrib.sessions import middleware
from django.conf import settings
from django.utils.importlib import import_module


class SubDomainSessionMiddleware(middleware.SessionMiddleware):
    def process_request(self, request):
        engine = import_module(settings.SESSION_ENGINE)
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
        if session_key is None:
            # Look for old cookie in request for auth purposes.
            session_key = request.COOKIES.get('sessionid', None)
        request.session = engine.SessionStore(session_key)

class ApiDisableCsrf(object):

    # Disable csrf for API requests
    def process_request(self, request):
        url_parts = request.path.split('/')

        if url_parts[1] == 'api':
            setattr(request, '_dont_enforce_csrf_checks', True)