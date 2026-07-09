import parler.appsettings
from django.db import connection
from memoize import delete_memoized, memoize
from parler.utils.conf import add_default_language_settings

from bluebottle.utils.models import TIMEOUT, get_default_language, get_languages

PARLER_SITE_ID = 1


def _tenant_schema_name():
    return getattr(getattr(connection, 'tenant', None), 'schema_name', 'public')


def _tenant_cache_name(fname, *args, **kwargs):
    return f'{fname}_{_tenant_schema_name()}'


@memoize(timeout=TIMEOUT, make_name=_tenant_cache_name)
def _parler_languages():
    languages = get_languages()

    return add_default_language_settings({
        PARLER_SITE_ID: [{'code': lang.full_code} for lang in languages],
        'default': {
            'fallbacks': [lang.full_code for lang in languages],
            'hide_untranslated': False
        }
    })


def parler_getattr(name):
    if name == 'PARLER_LANGUAGES':
        return _parler_languages()

    if name == 'PARLER_DEFAULT_LANGUAGE_CODE':
        return get_default_language()

    raise AttributeError(name)


def clear_parler_cache():
    delete_memoized(_parler_languages)


parler.appsettings.__getattr__ = parler_getattr
del parler.appsettings.PARLER_LANGUAGES
del parler.appsettings.PARLER_DEFAULT_LANGUAGE_CODE
