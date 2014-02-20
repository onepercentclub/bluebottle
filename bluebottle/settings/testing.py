from .base import *
from .secrets import *

COMPRESS_ENABLED = False

TEST_RUNNER = "colortools.test.ColorDjangoTestSuiteRunner"

SECRET_KEY = 'Testing'

INSTALLED_APPS += (
    'bluebottle.test',
)

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
COMPRESS_ENABLED = False

AUTH_USER_MODEL = 'test.TestBaseUser'
PROJECTS_PROJECT_MODEL = 'test.TestBaseProject'
ORGANIZATIONS_ORGANIZATION_MODEL = 'test.TestOrganization'
TASKS_TASK_MODEL = 'test.TestTask'

SOUTH_TESTS_MIGRATE = True

ROOT_URLCONF = 'bluebottle.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

INSTALLED_APPS += (
    'django_extensions',
    'colortools',
)
