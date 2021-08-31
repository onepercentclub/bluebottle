import parler.appsettings
from parler.utils.conf import add_default_language_settings

from bluebottle.utils.models import get_languages, get_default_language


def getattr(name):
    if name == 'PARLER_LANGUAGES':
        languages = get_languages()

        return add_default_language_settings({
            1: [{'code': lang.full_code} for lang in languages],
            'default': {
                'fallbacks': [lang.full_code for lang in languages],
                'hide_untranslated': False
            }
        })

    if name == 'PARLER_DEFAULT_LANGUAGE_CODE':
        return get_default_language()

    raise AttributeError(f"module 'parler.appsettings' has no attribute '{name}'")


parler.appsettings.__getattr__ = getattr
del parler.appsettings.PARLER_LANGUAGES
del parler.appsettings.PARLER_DEFAULT_LANGUAGE_CODE
