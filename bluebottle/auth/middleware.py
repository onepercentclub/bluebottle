from django.contrib.sessions.middleware import SessionMiddleware
from django.core.urlresolvers import reverse


"""
Only do the cookie session stuff for admin urls.
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
Disable csrf for non-Admin requests, eg API
"""
class AdminOnlyCsrf(object):
    def process_request(self, request):
        if not request.path.startswith(reverse('admin:index')):
            setattr(request, '_dont_enforce_csrf_checks', True)