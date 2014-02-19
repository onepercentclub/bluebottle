from .base import *
from .secrets import *

COMPRESS_ENABLED = False

INSTALLED_APPS += (
    'bluebottle.test',
)

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

COMPRESS_ENABLED = False
