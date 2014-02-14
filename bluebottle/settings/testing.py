from .base import *

SECRET_KEY = 'nfjeknfjknsjkfnwjknfklslflaejfleajfeslfjs'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}


INSTALLED_APPS += (
    'bluebottle.test',
)

AUTH_USER_MODEL = 'test.TestBaseUser'
PROJECTS_PROJECT_MODEL = 'test.TestBaseProject'
ORGANIZATIONS_ORGANIZATION_MODEL = 'test.TestOrganization'
TASKS_TASK_MODEL = 'test.TestTask'

SOUTH_TESTS_MIGRATE = False
