from .base import *

SECRET_KEY = 'nfjeknfjknsjkfnwjknfklslflaejfleajfeslfjs'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

SOUTH_TESTS_MIGRATE = False
