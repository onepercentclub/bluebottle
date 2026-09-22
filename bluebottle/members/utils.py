from datetime import datetime
from calendar import timegm
from builtins import str
from bluebottle.clients import properties


def get_jwt_secret(user):
    return properties.TENANT_JWT_SECRET + (str(user.last_logout) if user.last_logout else '')


import uuid
from rest_framework_jwt.settings import api_settings


def jwt_payload_handler(user):

    payload = {
        'username': user.pk,
        'exp': datetime.utcnow() + properties.JWT_EXPIRATION_DELTA
    }
    if isinstance(user.pk, uuid.UUID):
        payload['user_id'] = str(user.pk)

    # Include original issued at time for a brand new token,
    # to allow token refresh
    if api_settings.JWT_ALLOW_REFRESH:
        payload['orig_iat'] = timegm(
            datetime.utcnow().utctimetuple()
        )

    if api_settings.JWT_AUDIENCE is not None:
        payload['aud'] = api_settings.JWT_AUDIENCE

    if api_settings.JWT_ISSUER is not None:
        payload['iss'] = api_settings.JWT_ISSUER

    return payload


def jwt_is_impersonated(request):
    if not request:
        return False

    payload = None
    auth = getattr(request, 'auth', None)
    if isinstance(auth, dict):
        payload = auth
    elif auth:
        try:
            payload = api_settings.JWT_DECODE_HANDLER(auth)
        except Exception:
            payload = None

    if payload is None:
        header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION', '')
        if not header.startswith('JWT '):
            return False
        try:
            payload = api_settings.JWT_DECODE_HANDLER(header.split(' ', 1)[1])
        except Exception:
            return False

    return bool(payload.get('impersonated'))
