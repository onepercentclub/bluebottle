from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.core.urlresolvers import reverse
from rest_framework import exceptions
from rest_framework_jwt.authentication import JSONWebTokenAuthentication


class UserJwtTokenMiddleware:
    """
    Custom middleware to set the User on the request when using Jwt Token authentication.
    """
    def process_request(self, request):
        """ Override only the request to add the user """
        try:
            return request.user
        except AttributeError:
            pass

        obj = JSONWebTokenAuthentication()

        try:
            user_auth_tuple = obj.authenticate(request)
        except exceptions.APIException:
            user_auth_tuple = None

        if not user_auth_tuple is None:
            request.user, _auth = user_auth_tuple
            return


class AdminOnlySessionMiddleware(SessionMiddleware):
    """
    Only do the session stuff for admin urls.
    The frontend relies on auth tokens.
    """
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


class AdminOnlyAuthenticationMiddleware(AuthenticationMiddleware):
    """
    Only do the session authentication stuff for admin urls.
    The frontend relies on auth tokens so we clear the user.
    """
    def process_request(self, request):
        if request.path.startswith(reverse('admin:index')):
            super(AdminOnlyAuthenticationMiddleware, self).process_request(request)


class AdminOnlyCsrf(object):
    """
    Disable csrf for non-Admin requests, eg API
    """
    def process_request(self, request):
        if not request.path.startswith(reverse('admin:index')):
            setattr(request, '_dont_enforce_csrf_checks', True)