from calendar import timegm
from datetime import datetime, timedelta
import json
import logging

from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render_to_response
from django.utils import timezone

from rest_framework import exceptions
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.settings import api_settings

from lockdown.middleware import (LockdownMiddleware as BaseLockdownMiddleware,
                                 _default_url_exceptions, _default_form)

from lockdown import settings as lockdown_settings
from bluebottle.utils.utils import get_client_ip


LAST_SEEN_DELTA = 10  # in minutes


def isAdminRequest(request):
    admin_base = reverse('admin:index')

    return request.path.startswith(admin_base)


class UserJwtTokenMiddleware:
    """
    Custom middleware to set the User on the request when using
    Jwt Token authentication.
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

        if user_auth_tuple is not None:
            request.user, _ = user_auth_tuple

            # Set last_seen on the user record if it has been > 10 mins
            # since the record was set.
            if not request.user.last_seen or (request.user.last_seen <
               timezone.now() - timedelta(minutes=LAST_SEEN_DELTA)):
                request.user.last_seen = timezone.now()
                request.user.save()
            return


class SlidingJwtTokenMiddleware:
    """
    Custom middleware to set a sliding window for the jwt auth token expiration.
    """

    def process_response(self, request, response):
        """ Override only the request to add the new token """
        obj = JSONWebTokenAuthentication()

        try:
            user_auth_tuple = obj.authenticate(request)
        except exceptions.APIException:
            user_auth_tuple = None

        # Check if request includes valid token
        if user_auth_tuple is not None:
            user, _auth = user_auth_tuple

            # Get the payload details
            jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
            payload = jwt_decode_handler(_auth)
            logging.debug('JWT payload found: {0}'.format(payload))

            # Check whether we need to renew the token. This will happen if the token
            # hasn't been renewed in JWT_TOKEN_RENEWAL_DELTA
            exp = payload.get('exp')
            created_timestamp = exp - int(
                api_settings.JWT_EXPIRATION_DELTA.total_seconds())
            renewal_timestamp = created_timestamp + int(
                settings.JWT_TOKEN_RENEWAL_DELTA.total_seconds())
            now_timestamp = timegm(datetime.utcnow().utctimetuple())

            # If it has been less than JWT_TOKEN_RENEWAL_DELTA time since the
            # token was created then we will pass on created a renewed token
            # and just return the response unchanged.
            if now_timestamp < renewal_timestamp:
                logging.debug(
                    'JWT_TOKEN_RENEWAL_DELTA not exceeded: returning response unchanged.')
                return response

            # Get and check orig_iat
            orig_iat = payload.get('orig_iat')
            if orig_iat:
                # verify expiration
                expiration_timestamp = orig_iat + int(
                    api_settings.JWT_TOKEN_RENEWAL_LIMIT.total_seconds())
                if now_timestamp > expiration_timestamp:
                    # Token has passed renew time limit - just return existing
                    # response. We need to test this process because it is
                    # probably the case that the response has already been
                    # set to an unauthorized status
                    # now_timestamp > expiration_timestamp.
                    logging.debug(
                        'JWT token has expired: returning response unchanged.')
                    return response

            else:
                # orig_iat field is required - just return existing response
                logging.debug(
                    'JWT token orig_iat field not defined: returning response unchanged.')
                return response

            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            new_payload = jwt_payload_handler(user)
            new_payload['orig_iat'] = orig_iat

            # Attach the renewed token to the response
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            response['Refresh-Token'] = "JWT {0}".format(
                jwt_encode_handler(new_payload))

            logging.debug('JWT token has been renewed.')

            return response

        else:
            # No authenticated user - just return existing response
            logging.debug(
                'No JWT authenticated user: returning response unchanged.')
            return response


class AdminOnlySessionMiddleware(SessionMiddleware):
    """
    Only do the session stuff for admin urls.
    The frontend relies on auth tokens.
    """

    def process_request(self, request):
        if isAdminRequest(request):
            super(AdminOnlySessionMiddleware, self).process_request(request)
        else:
            return

    def process_response(self, request, response):
        if isAdminRequest(request):
            return super(AdminOnlySessionMiddleware, self).process_response(
                request, response)
        else:
            return response


class AdminOnlyAuthenticationMiddleware(AuthenticationMiddleware):
    """
    Only do the session authentication stuff for admin urls.
    The frontend relies on auth tokens so we clear the user.
    """

    def process_request(self, request):
        if isAdminRequest(request):
            super(AdminOnlyAuthenticationMiddleware, self).process_request(
                request)


class AdminOnlyCsrf(object):
    """
    Disable csrf for non-Admin requests, eg API
    """

    def process_request(self, request):
        if not isAdminRequest(request):
            setattr(request, '_dont_enforce_csrf_checks', True)


class LockdownMiddleware(BaseLockdownMiddleware):
    """
    LockdownMiddleware taken from the Django Lockdown package with the addition
    of password coming from request header: X-Lockdown
    """

    def process_request(self, request):
        if 'HTTP_X_LOCKDOWN' not in request.META:
            return None

        try:
            session = request.session
        except AttributeError:
            raise ImproperlyConfigured('django-lockdown requires the Django '
                                       'sessions framework')

        # Don't lock down if the URL matches an exception pattern.
        if self.url_exceptions is None:
            url_exceptions = _default_url_exceptions
        else:
            url_exceptions = self.url_exceptions
        for pattern in url_exceptions:
            if pattern.search(request.path):
                return None

        # Don't lock down if outside of the lockdown dates.
        if self.until_date is None:
            until_date = lockdown_settings.UNTIL_DATE
        else:
            until_date = self.until_date
        if self.after_date is None:
            after_date = lockdown_settings.AFTER_DATE
        else:
            after_date = self.after_date
        if until_date or after_date:
            locked_date = False
            if until_date and datetime.datetime.now() < until_date:
                locked_date = True
            if after_date and datetime.datetime.now() > after_date:
                locked_date = True
            if not locked_date:
                return None

        if request.META.get('CONTENT_TYPE') == 'application/x-www-form-urlencoded' and request.method == 'POST':
            form_data = request.POST
        else:
            form_data = {}

        passwords = (request.META['HTTP_X_LOCKDOWN'],)

        if self.form is None:
            form_class = _default_form
        else:
            form_class = self.form

        form = form_class(passwords=passwords, data=form_data, **self.form_kwargs)

        authorized = False
        token = session.get(self.session_key)
        if hasattr(form, 'authenticate'):
            if form.authenticate(token):
                authorized = True
        elif token is True:
            authorized = True

        if authorized and self.logout_key and self.logout_key in request.GET:
            if self.session_key in session:
                del session[self.session_key]
            url = request.path
            querystring = request.GET.copy()
            del querystring[self.logout_key]
            if querystring:
                url = '%s?%s' % (url, querystring.urlencode())
            return self.redirect(request)

        # Don't lock down if the user is already authorized for previewing.
        if authorized:
            return None

        if form.is_valid():
            if hasattr(form, 'generate_token'):
                token = form.generate_token()
            else:
                token = True
            session[self.session_key] = token
            return self.redirect(request)

        page_data = {'until_date': until_date, 'after_date': after_date}
        if not hasattr(form, 'show_form') or form.show_form():
            page_data['form'] = form

        response = render_to_response('lockdown/form.html', page_data)
        response.status_code = 401
        return response


authorization_logger = logging.getLogger(__name__)


class LogAuthFailureMiddleWare:
    def process_request(self, request):
        request.body  # touch the body so that we have access to it in process_response

    def process_response(self, request, response):
        """ Log a message for each failed login attempt. """
        if reverse('admin:login') == request.path and request.method == 'POST' and response.status_code != 302:
            error = 'Authorization failed: {username} {ip}'.format(
                ip=get_client_ip(request), username=request.POST.get('username')
            )
            authorization_logger.error(error)

        if reverse('token-auth') == request.path and request.method == 'POST' and response.status_code != 200:
            try:
                data = json.loads(request.body)
            except ValueError:
                data = request.POST

            error = 'Authorization failed: {username} {ip}'.format(
                ip=get_client_ip(request), username=data.get('email')
            )
            authorization_logger.error(error)

        return response
