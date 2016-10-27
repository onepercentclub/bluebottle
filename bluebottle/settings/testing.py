import logging
import sys

SECRET_KEY = '1, 2, this is just a test!'

from .base import *
from bluebottle.payments_docdata.settings import *

import warnings

# Raise exception on naive datetime...
warnings.filterwarnings(
    'error',
    r"DateTimeField .* received a naive datetime",
    RuntimeWarning, r'django\.db\.models\.fields')


MERCHANT_ACCOUNTS = [
    {
        'merchant': 'docdata',
        'merchant_name': 'merchant_name',
        'merchant_password': 'merchant_password',
        'currency': 'EUR'
    },
]


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

SKIP_IP_LOOKUP = True

# Graphviz
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

from bluebottle.payments_mock.settings import (MOCK_PAYMENT_METHODS,
                                               MOCK_FEES)

PAYMENT_METHODS = MOCK_PAYMENT_METHODS
MINIMAL_PAYOUT_AMOUNT = 10
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

SEND_WELCOME_MAIL = False
SEND_MAIL = True


TEST_RUNNER = 'bluebottle.test.test_runner.MultiTenantRunner'
