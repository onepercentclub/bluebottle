from .base import *
from .secrets import *
from bluebottle.payments_docdata.settings import *

DOCDATA_MERCHANT_NAME = 'merchant_name'
DOCDATA_MERCHANT_PASSWORD = 'merchant_password'

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
        'ATOMIC_REQUESTS': True
	}
}

VAT_RATE = 21

DOCDATA_FEES = {
    'transaction': 0.20,
    'payment_methods': {
        'ideal': 0.35,
        'mastercard': '3.0%',
        'visa': '3.5%',
        'paypal': '3.5%',
        'sepa_direct_debit': 0.25
    }
}

PAYMENT_METHODS = (
    {
        'provider': 'docdata',
        'id': 'docdata-creditcard',
        'profile': 'creditcard',
        'name': 'CreditCard',
        'supports_recurring': False,
    },
    {
        'provider': 'docdata',
        'id': 'docdata-ideal',
        'profile': 'ideal',
        'name': 'iDEAL',
        'restricted_countries': ('NL', 'Netherlands'),
        'supports_recurring': False,
    },
)