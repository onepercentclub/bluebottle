from .base import *

SECRET_KEY = 'nfjeknfjknsjkfnwjknfklslflaejfleajfeslfjs'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

INSTALLED_APPS += (
    'bluebottle.bb_projects.tests.testproject',
)

#AUTH_USER_MODEL = "baseuser.TestBaseUser"
PROJECTS_PROJECT_MODEL = 'testproject.TestBaseProject'
SOUTH_TESTS_MIGRATE = False
