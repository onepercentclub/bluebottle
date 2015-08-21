from calendar import timegm
from datetime import datetime
import logging

from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.core.urlresolvers import reverse
from django.conf import settings

from rest_framework import exceptions
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.settings import api_settings


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
        if not user_auth_tuple is None:
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

            # If it has been less than JWT_TOKEN_RENEWAL_DELTA time since the token was created then
            # we will pass on created a renewed token and just return the response unchanged.
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
                    # Token has passed renew time limit - just return existing response. We need to test 
                    # this process because it is probably the case that the response has already been
                    # set to an unauthorized status now_timestamp > expiration_timestamp.
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
        if request.path.startswith(reverse('admin:index')):
            super(AdminOnlySessionMiddleware, self).process_request(request)
        else:
            return

    def process_response(self, request, response):
        if request.path.startswith(reverse('admin:index')):
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
        if request.path.startswith(reverse('admin:index')):
            super(AdminOnlyAuthenticationMiddleware, self).process_request(
                request)


class AdminOnlyCsrf(object):
    """
    Disable csrf for non-Admin requests, eg API
    """

    def process_request(self, request):
        if not request.path.startswith(reverse('admin:index')):
            setattr(request, '_dont_enforce_csrf_checks', True)
