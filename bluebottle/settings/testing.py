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
    'bluebottle.bb_organizations.tests.testorganization',
)

#AUTH_USER_MODEL = "baseuser.TestBaseUser"
PROJECTS_PROJECT_MODEL = 'testproject.TestBaseProject'
ORGANIZATIONS_ORGANIZATION_MODEL = 'testorganization.TestOrganization'
SOUTH_TESTS_MIGRATE = False
