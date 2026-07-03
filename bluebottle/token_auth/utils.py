from django.conf import settings
from django.utils.module_loading import import_string

from django.core.exceptions import ImproperlyConfigured


def get_settings():
    from bluebottle.members.sso import get_token_auth_settings

    try:
        return get_token_auth_settings()
    except ImproperlyConfigured:
        pass

    properties_path = getattr(settings,
                              'TOKEN_AUTH_SETTINGS',
                              'django.conf.settings')

    try:
        properties = import_string(properties_path)
    except ImportError as e:
        raise ImproperlyConfigured(e)

    try:
        return properties.TOKEN_AUTH
    except AttributeError:
        raise ImproperlyConfigured(
            'Missing TOKEN_AUTH attribute in {}'.format(properties_path)
        )
