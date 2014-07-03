from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.core.urlresolvers import reverse


"""
Only do the session stuff for admin urls.
The frontend relies on auth tokens.
"""
class AdminOnlySessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        if request.path.startswith(reverse('admin:index')):
            super(AdminOnlySessionMiddleware, self).process_request(request)
        else:
            return

    def process_response(self, request, response):
        if request.path.startswith(reverse('admin:index')):
            return super(AdminOnlySessionMiddleware, self).process_response(request, response)
        else:
            return response


"""
Only do the session authentication stuff for admin urls.
The frontend relies on auth tokens so we clear the user.
"""
class AdminOnlyAuthenticationMiddleware(AuthenticationMiddleware):
    def process_request(self, request):
        if request.path.startswith(reverse('admin:index')):
            super(AdminOnlyAuthenticationMiddleware, self).process_request(request)


"""
Disable csrf for non-Admin requests, eg API
"""
class AdminOnlyCsrf(object):
    def process_request(self, request):
        if not request.path.startswith(reverse('admin:index')):
            setattr(request, '_dont_enforce_csrf_checks', True)