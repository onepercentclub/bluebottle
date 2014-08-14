from bluebottle.settings.base import *


SECRET_KEY = '8t(nq%rdBHRi7b5bveU^%Erbfu76yr^%uveDU546tedib#%uRD91OLJTdf'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS += (
    'bluebottle.test',
)

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
COMPRESS_ENABLED = False

SOUTH_TESTS_MIGRATE = True

ROOT_URLCONF = 'bluebottle.urls'
