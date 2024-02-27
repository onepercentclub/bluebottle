# flake8: noqa

from .testing import *

DATABASES = {
    'default': {
        "ENGINE": "bluebottle.clients.postgresql_backend",
        'HOST': 'localhost',
        'PORT': '5432',
        'NAME': 'bluebottle_test',
        'USER': 'bb',
        'PASSWORD': 'bb'
    }
}

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

DEBUG = False
