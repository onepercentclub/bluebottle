from .base import *
from .secrets import *


INSTALLED_APPS += (
    'bluebottle.test',
)

AUTH_USER_MODEL = 'test.TestBaseUser'
PROJECTS_PROJECT_MODEL = 'test.TestBaseProject'
ORGANIZATIONS_ORGANIZATION_MODEL = 'test.TestOrganization'
TASKS_TASK_MODEL = 'test.TestTask'

SOUTH_TESTS_MIGRATE = True

ROOT_URLCONF = 'bluebottle.urls'
