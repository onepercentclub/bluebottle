import parler.appsettings
from parler.utils.conf import add_default_language_settings

from bluebottle.utils.models import Language


def getattr(name):
    if name == 'PARLER_LANGUAGES':
        languages = Language.objects.all()

        return add_default_language_settings({
            1: [{'code': lang.code} for lang in languages],
            'default': {
                'fallbacks': [lang.code for lang in languages],
                'hide_untranslated': False
            }
        })

    if name == 'PARLER_DEFAULT_LANGUAGE_CODE':
        default = Language.objects.filter(default=True).first()
        if default:
            return default.code
        else:
            return 'en'

    raise AttributeError(f"module 'parler.appsettings' has no attribute '{name}'")


parler.appsettings.__getattr__ = getattr
del parler.appsettings.PARLER_LANGUAGES
del parler.appsettings.PARLER_DEFAULT_LANGUAGE_CODE
