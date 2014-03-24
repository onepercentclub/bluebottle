from .base import *
from .secrets import *


INSTALLED_APPS += (
    'bluebottle.test',
    'django_extensions',
)

# Set up a proper testing email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
COMPRESS_ENABLED = False

# Include the tests models
INCLUDE_TEST_MODELS = True

# Define the models to use for testing
AUTH_USER_MODEL = 'test.TestBaseUser'
PROJECTS_PROJECT_MODEL = 'test.TestBaseProject'
ORGANIZATIONS_ORGANIZATION_MODEL = 'test.TestOrganization'
TASKS_TASK_MODEL = 'test.TestTask'
TASKS_SKILL_MODEL = 'test.TestSkill'
TASKS_TASKMEMBER_MODEL = 'test.TestTaskMember'
TASKS_TASKFILE_MODEL = 'test.TestTaskFile'
ORGANIZATIONS_DOCUMENT_MODEL = 'test.TestOrganizationDocument'
ORGANIZATIONS_MEMBER_MODEL = 'test.TestOrganizationMember'

# Yes, activate the South migrations. Otherwise, we'll never notice if our
# code screwed up the database synchronization
SOUTH_TESTS_MIGRATE = True

ROOT_URLCONF = 'bluebottle.urls'

#Graphviz
GRAPH_MODELS = {
  'all_applications': True,
  'group_models': True,
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': ':memory:',
#     },
# }