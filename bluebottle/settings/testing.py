from .base import *
from .secrets import *

TEST_RUNNER = 'discover_runner.DiscoverRunner'

INSTALLED_APPS += (
    'django_extensions',
)

# Set up a proper testing email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
COMPRESS_ENABLED = False

# Include the tests models
INCLUDE_TEST_MODELS = True

# Yes, activate the South migrations. Otherwise, we'll never notice if our
# code screwed up the database synchronization
SOUTH_TESTS_MIGRATE = True

ROOT_URLCONF = 'bluebottle.urls'

#Graphviz
GRAPH_MODELS = {
  'all_applications': True,
  'group_models': True,
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}