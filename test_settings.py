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

INCLUDE_TEST_MODELS = True

AUTH_USER_MODEL = 'test.TestBaseUser'

PROJECTS_PROJECT_MODEL = 'test.TestBaseProject'
PROJECTS_PHASELOG_MODEL = 'test.TestBaseProjectPhaseLog'
FUNDRAISERS_FUNDRAISER_MODEL = 'test.TestFundRaiser'

TASKS_TASK_MODEL = 'test.TestTask'
TASKS_SKILL_MODEL = 'test.TestSkill'
TASKS_TASKMEMBER_MODEL = 'test.TestTaskMember'
TASKS_TASKFILE_MODEL = 'test.TestTaskFile'

ORGANIZATIONS_ORGANIZATION_MODEL = 'test.TestOrganization'
ORGANIZATIONS_DOCUMENT_MODEL = 'test.TestOrganizationDocument'
ORGANIZATIONS_MEMBER_MODEL = 'test.TestOrganizationMember'

DONATIONS_DONATION_MODEL = 'test.TestDonation'
ORDERS_ORDER_MODEL = 'test.TestOrder'

SOUTH_TESTS_MIGRATE = True

ROOT_URLCONF = 'bluebottle.urls'
