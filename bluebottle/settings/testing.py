# flake8: noqa

SECRET_KEY = '1, 2, this is just a test!'


RECAPTCHA_PRIVATE_KEY = 'test-private-key'
RECAPTCHA_PUBLIC_KEY = 'test-public-key'

from .base import *

import warnings
import logging

# Raise exception on naive datetime...
warnings.filterwarnings(
    'error',
    r"DateTimeField .* received a naive datetime",
    RuntimeWarning, r'django\.db\.models\.fields')

CSRF_COOKIE_SECURE = False
ALLOWED_HOSTS = ['*']

SUPPORT_EMAIL_ADDRESSES = [
    'support@example.com',
    'helpdesk@example.com',
]

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
        'HOST': 'localhost',
        'PORT': '5432',
        'NAME': 'bluebottle_test',
        'USER': 'testuser',
        'PASSWORD': 'password'
    }
}

# used in migrations to indicate that db extensions should be created
CREATE_DB_EXTENSIONS = True

DATABASE_ROUTERS = (
    'tenant_schemas.routers.TenantSyncRouter',
)

PAYMENT_METHODS = (
    {
        'provider': 'mock',
        'id': 'mock-paypal',
        'profile': 'paypal',
        'name': 'MockPal',
        'currencies': {
            'EUR': {'min_amount': 5, 'max_amount': 100}
        }
    },
    {
        'provider': 'mock',
        'id': 'mock-ideal',
        'profile': 'ideal',
        'name': 'MockDeal',
        'restricted_countries': ('NL',),
        'currencies': {
            'EUR': {'min_amount': 5},
            'USD': {'min_amount': 5},
        }
    },
    {
        'provider': 'mock',
        'id': 'mock-creditcard',
        'profile': 'creditcard',
        'name': 'MockCard',
        'currencies': {
            'USD': {'min_amount': 5},
        }
    }
)

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
BROKER_URL = 'memory://localhost'

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

# Optional local override for test settings
try:
    from _testing import *
except ImportError:
    pass

ELASTICSEARCH_DSL_AUTOSYNC = False
ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'django_elasticsearch_dsl.signals.RealTimeSignalProcessor'

STRIPE = {
    'secret_key': 'test-key',
    'webhook_secret_sources': 'test-webhook-secret',
    'webhook_secret_intents': 'test-webhook-secret',
    'webhook_secret_connect': 'test-webhook-secret-connect',
    'api_key': 'test-pub-key',
    'publishable_key': 'test-pub-key'
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'axes_cache': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

AXES_CACHE = 'axes_cache'
STATIC_MAPS_API_KEY = 'someinvalidapikey'
STATIC_MAPS_API_SECRET = 'fpqFpdo4RY9GDc-xxawF6Ipmp3Y='

DEFAULT_CURRENCY = 'EUR'

CONFLUENCE = {
    'api': {
        'domain': '',
        'user': '',
        'key': ''
    },
    'prod_models': [
        {
            'title': 'States - Initiative',
            'model': 'bluebottle.initiatives.models.Initiative',
            'page_id': ''
        },
    ],

    'dev_models': [

        # Initiative
        {
            'title': '[DEV] States - Initiative',
            'model': 'bluebottle.initiatives.models.Initiative',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Activity Organizer',
            'model': 'bluebottle.activities.models.Organizer',
            'page_id': ''
        },

        # Funding
        {
            'title': '[DEV] States - Funding - Donor',
            'model': 'bluebottle.funding.models.Donor',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Funding - Money Contribution',
            'model': 'bluebottle.funding.models.MoneyContribution',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Funding - Fundraising Campaign',
            'model': 'bluebottle.funding.models.Funding',
            'page_id': ''
        },

        {
            'title': '[DEV] States - Funding - Plain Payout Account',
            'model': 'bluebottle.funding.models.PlainPayoutAccount',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Funding - Stripe Payout Account',
            'model': 'bluebottle.funding_stripe.models.StripePayoutAccount',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Funding - Payout',
            'model': 'bluebottle.funding.models.Payout',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Funding - Stripe Source Payment',
            'model': 'bluebottle.funding_stripe.models.StripeSourcePayment',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Funding - Stripe Intent Payment',
            'model': 'bluebottle.funding_stripe.models.StripePayment',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Funding - Pledge Payment',
            'model': 'bluebottle.funding_pledge.models.PledgePayment',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Funding - Flutterwave Payment',
            'model': 'bluebottle.funding_flutterwave.models.FlutterwavePayment',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Funding - Lipisha Payment',
            'model': 'bluebottle.funding_lipisha.models.LipishaPayment',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Funding - Vitepay Payment',
            'model': 'bluebottle.funding_vitepay.models.VitepayPayment',
            'page_id': ''
        },

        {
            'title': '[DEV] States - Funding - Stripe External Account',
            'model': 'bluebottle.funding_stripe.models.ExternalAccount',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Funding - Pledge Bank Account',
            'model': 'bluebottle.funding_pledge.models.PledgeBankAccount',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Funding - Flutterwave Bank Account',
            'model': 'bluebottle.funding_flutterwave.models.FlutterwaveBankAccount',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Funding - Lipisha Bank Account',
            'model': 'bluebottle.funding_lipisha.models.LipishaBankAccount',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Funding - Vitepay Bank Account',
            'model': 'bluebottle.funding_vitepay.models.VitepayBankAccount',
            'page_id': ''
        },

        # Time-based Activities
        {
            'title': '[DEV] States - Time based - Activity on a date',
            'model': 'bluebottle.time_based.models.DateActivity',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Time based - Participant on a date',
            'model': 'bluebottle.time_based.models.DateParticipant',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Time based - Activity slot',
            'model': 'bluebottle.time_based.models.DateActivitySlot',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Time based - Slot participant',
            'model': 'bluebottle.time_based.models.SlotParticipant',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Time based - Deadline Activity',
            'model': 'bluebottle.time_based.models.DeadlineActivity',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Time based - Periodic Activity',
            'model': 'bluebottle.time_based.models.PeriodicActivity',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Time based - Deadline Participant',
            'model': 'bluebottle.time_based.models.DeadlineParticipant',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Time based - Periodic Participant',
            'model': 'bluebottle.time_based.models.PeriodicParticipant',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Time based - Time contribution',
            'model': 'bluebottle.time_based.models.TimeContribution',
            'page_id': ''
        },

        # Deed Activities
        {
            'title': '[DEV] States - Deeds - Deed',
            'model': 'bluebottle.deeds.models.Deed',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Deeds - Deed Participant',
            'model': 'bluebottle.deeds.models.DeedParticipant',
            'page_id': ''
        },

        # Collection Activities
        {
            'title': '[DEV] States - Collect - Collection activity',
            'model': 'bluebottle.collect.models.CollectActivity',
            'page_id': ''
        },
        {
            'title': '[DEV] States - Collect - Collection contributor',
            'model': 'bluebottle.collect.models.CollectContributor',
            'page_id': ''
        },

    ]}

RANDOM_IMAGE_PROVIDER = "https://picsum.photos/seed/{seed}/{width}/{height}"
