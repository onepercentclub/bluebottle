from datetime import datetime
from calendar import timegm
from builtins import str
from bluebottle.clients import properties


def get_jwt_secret(user):
    return properties.SECRET_KEY + (str(user.last_logout) if user.last_logout else '')


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
