# flake8: noqa

SECRET_KEY = '1, 2, this is just a test!'

from .base import *
from bluebottle.payments_docdata.settings import *

import warnings
import logging

# Raise exception on naive datetime...
warnings.filterwarnings(
    'error',
    r"DateTimeField .* received a naive datetime",
    RuntimeWarning, r'django\.db\.models\.fields')

CSRF_COOKIE_SECURE = False
ALLOWED_HOSTS = ['*']

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

INSTALLED_APPS += ('bluebottle.payments_mock',)

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
        "ENGINE": "bluebottle.clients.postgresql_backend",
        'HOST': '',
        'PORT': '',
        'NAME': 'bluebottle_test',
        'USER': '',
        'PASSWORD': ''
    }
}

# used in migrations to indicate that db extensions should be created
CREATE_DB_EXTENSIONS = True

DATABASE_ROUTERS = (
    'tenant_schemas.routers.TenantSyncRouter',
)

TENANT_APPS += (
    'bluebottle.payments_mock',
)

from bluebottle.payments_mock.settings import MOCK_PAYMENT_METHODS

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

SEND_WELCOME_MAIL = False
SEND_MAIL = True


PAYOUT_METHODS = [
    {
        'method': 'duckbank',
        'payment_methods': [
            'duck-directdebit',
            'duck-creditcard',
            'duck-ideal'
        ],
        'currencies': ['EUR'],
        'account_name': "Dagobert Duck",
        'account_bic': "DUCKNL2U",
        'account_iban': "NL12DUCK0123456789"
    },
    {
        'method': 'excel',
        'payment_methods': [
            'vitepay-orangemoney',
            'interswitch-webpay',
            'pledge-standard'
        ],
        'currencies': ['XOF', 'CFA', 'USD', 'EUR']
    }
]

PAYOUT_SERVICE = {
    'service': 'dorado',
    'url': 'test'
}


TEST_RUNNER = 'bluebottle.test.test_runner.MultiTenantRunner'
NUM_SLOW_TESTS = 50

DEBUG = False
TEMPLATE_DEBUG = False
logging.disable(logging.CRITICAL)

CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
BROKER_BACKEND = 'memory'

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

# Optional local override for test settings
try:
    from _testing import *
except ImportError:
    pass

ELASTICSEARCH_DSL_AUTOSYNC = False

STRIPE = {
    'secret_key': 'test-key',
    'webhook_secret': 'test-webhook-secret',
    'webhook_secret_connect': 'test-webhook-secret-connect',
    'api_key': 'test-pub-key',
    'publishable_key': 'test-pub-key'
}
