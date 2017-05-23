import parler.appsettings
from parler.utils.conf import add_default_language_settings

from bluebottle.clients import properties

appsettings = parler.appsettings


class TenantAwareParlerAppsettings(object):
    @property
    def PARLER_DEFAULT_LANGUAGE_CODE(self):
        return properties.LANGUAGE_CODE

    @property
    def PARLER_LANGUAGES(self):
        return add_default_language_settings({
            1: [{'code': lang[0]} for lang in properties.LANGUAGES],
            'default': {
                'fallbacks': [properties.LANGUAGE_CODE],
                'hide_untranslated': False
            }
        })

    def __getattr__(self, attr):
        return getattr(appsettings, attr)


parler.appsettings = TenantAwareParlerAppsettings()
