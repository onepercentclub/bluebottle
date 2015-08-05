from .base import *
from .secrets import *
from bluebottle.payments_docdata.settings import *

# Supress naive date warnings
import warnings
warnings.filterwarnings(
        'ignore', r"DateTimeField received a naive datetime .* while time zone support is active",
        RuntimeWarning, r'django\.db\.models\.fields')


DOCDATA_MERCHANT_NAME = 'merchant_name'
DOCDATA_MERCHANT_PASSWORD = 'merchant_password'


# Set up a proper testing email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
COMPRESS_ENABLED = False

# Include the tests models
INCLUDE_TEST_MODELS = True

INSTALLED_APPS += (
    'bluebottle.payments_mock',
)

# Yes, activate the South migrations. Otherwise, we'll never notice if our
# code screwed up the database synchronization
SOUTH_TESTS_MIGRATE = False

ROOT_URLCONF = 'bluebottle.urls'


#Graphviz
GRAPH_MODELS = {
  'all_applications': True,
  'group_models': True,
}

DEFAULT_DB_ALIAS = 'default'
DATABASES = {
    'default': {
        'ENGINE': 'tenant_schemas.postgresql_backend',
        'HOST': '',
        'PORT': '',
        'NAME': 'bluebottle_test',
        'USER': '',
        'PASSWORD': ''
    }
}

DATABASE_ROUTERS = (
    'tenant_schemas.routers.TenantSyncRouter',
)

TENANT_APPS += (
    'bluebottle.payments_mock',
)

INSTALLED_APPS = TENANT_APPS + SHARED_APPS + ('django_nose', 'tenant_schemas',)

from bluebottle.payments_mock.settings import (MOCK_PAYMENT_METHODS,
                                               MOCK_FEES)
PAYMENT_METHODS = MOCK_PAYMENT_METHODS

DOCDATA_FEES = {
    'transaction': 0.15,
    'payment_methods': {
        'ideal': 0.25,
        'mastercard': '2.5%',
        'visa': '2.5%',
        'amex': '2.5%',
        'sepa_direct_debit': 0.13
    }
}

RECURRING_DONATIONS_ENABLED = True
