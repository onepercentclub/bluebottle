# Django settings for BlueBottle project.

import os, datetime

PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir))

DEBUG = True
TEMPLATE_DEBUG = DEBUG
COMPRESS_ENABLED = False
INCLUDE_TEST_MODELS = True

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Amsterdam'

# Available user interface translations
# Ref: https://docs.djangoproject.com/en/1.4/ref/settings/#languages
#
# Default language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

# This is defined here as a do-nothing function because we can't import
# django.utils.translation -- that module depends on the settings.
gettext_noop = lambda s: s

LANGUAGES = (
    ('nl', gettext_noop('Dutch')),
    ('en', gettext_noop('English')),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'static', 'media')

# Absolute filesystem path to the directory that will hold PRIVATE user-uploaded files.
PRIVATE_MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'private', 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static', 'assets')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/assets/'

STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    # You can also name this tuple like: ('css', '/path/to/css')
    (os.path.join(PROJECT_ROOT, 'static', 'global')),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)

TEMPLATE_DIRS = (
    (os.path.join(PROJECT_ROOT, 'templates')),
)



MIDDLEWARE_CLASSES = (
    'bluebottle.auth.middleware.UserJwtTokenMiddleware',
    'bluebottle.auth.middleware.AdminOnlyCsrf',
    'bluebottle.utils.middleware.SubDomainSessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'bluebottle.auth.middleware.AdminOnlySessionMiddleware',
    'bluebottle.auth.middleware.AdminOnlyAuthenticationMiddleware',
    'bluebottle.bb_accounts.middleware.LocaleMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django_tools.middlewares.ThreadLocal.ThreadLocalMiddleware',
    'bluebottle.auth.middleware.SlidingJwtTokenMiddleware'
)

REST_FRAMEWORK = {
    # Don't do basic authentication.
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
}

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(hours=12)
}

JWT_TOKEN_RENEWAL_DELTA = datetime.timedelta(minutes=30)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',

    # BlueBottle dependencies.
    'compressor',
    'registration',
    'rest_framework',
    'taggit',
    'south',
    'sorl.thumbnail',

    # BlueBottle applications.
    'bluebottle.bb_accounts',
    'bluebottle.bb_organizations',
    'bluebottle.bb_projects',
    'bluebottle.bb_tasks',
    'bluebottle.bb_fundraisers',
    'bluebottle.bb_orders',
    'bluebottle.bb_donations',
    'bluebottle.bb_payouts',

    # Other Bb apps
    'bluebottle.common',
    'bluebottle.contact',
    'bluebottle.contentplugins',
    'bluebottle.geo',
    'bluebottle.news',
    'bluebottle.pages',
    'bluebottle.quotes',
    'bluebottle.slides',
    'bluebottle.redirects',
    'bluebottle.terms',
    'bluebottle.utils',
    'bluebottle.wallposts',

    # Basic Bb implementations
    'bluebottle.fundraisers',
    'bluebottle.orders',
    'bluebottle.donations',
    'bluebottle.payouts',

    'bluebottle.payments',
    'bluebottle.payments_docdata',
    'bluebottle.payments_mock',
    'bluebottle.payments_logger',
    'bluebottle.payments_voucher',

    'bluebottle.bb_follow',

    # Test Bb implementations
    'bluebottle.test',

    # Modules required by BlueBottle
    'fluent_contents',
    'fluent_contents.plugins.text',
    'fluent_contents.plugins.oembeditem',
    'fluent_contents.plugins.rawhtml',

    'django_wysiwyg',
    'templatetag_handlebars',

    'raven.contrib.django.raven_compat',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'bluebottle.utils.context_processors.installed_apps_context_processor',
)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'


THUMBNAIL_DEBUG = True
THUMBNAIL_QUALITY = 85


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'sentry': {
            'level': 'INFO',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'payment_logs': {
            'level': 'INFO',
            'class': 'bluebottle.payments_logger.handlers.PaymentLogHandler',
        }
    },
    'loggers': {
        'payments.payment': {
            'handlers': ['mail_admins', 'payment_logs', 'sentry'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


# Define the models to use for testing
AUTH_USER_MODEL = 'test.TestBaseUser'

PROJECTS_PROJECT_MODEL = 'test.TestBaseProject'
PROJECTS_PHASELOG_MODEL = 'test.TestBaseProjectPhaseLog'

FUNDRAISERS_FUNDRAISER_MODEL = 'fundraisers.Fundraiser'

TASKS_TASK_MODEL = 'test.TestTask'
TASKS_SKILL_MODEL = 'test.TestSkill'
TASKS_TASKMEMBER_MODEL = 'test.TestTaskMember'
TASKS_TASKFILE_MODEL = 'test.TestTaskFile'

ORGANIZATIONS_ORGANIZATION_MODEL = 'test.TestOrganization'
ORGANIZATIONS_DOCUMENT_MODEL = 'test.TestOrganizationDocument'
ORGANIZATIONS_MEMBER_MODEL = 'test.TestOrganizationMember'

DONATIONS_DONATION_MODEL = 'donations.Donation'
ORDERS_ORDER_MODEL = 'orders.Order'

PAYOUTS_PROJECTPAYOUT_MODEL = 'payouts.ProjectPayout'
PAYOUTS_ORGANIZATIONPAYOUT_MODEL = 'payouts.OrganizationPayout'


# Required for handlebars_template to work properly
USE_EMBER_STYLE_ATTRS = True


PROJECT_PHASES = (
    ('Plan', (
        ('plan-new', 'Plan - New'),
        ('plan-submitted', 'Plan - Submitted'),
        ('plan-needs-work', 'Plan - Needs work'),
        ('plan-rejected', 'Plan - Rejected'),
        ('plan-approved', 'Plan - Approved'),
    )),
    ('Campaign', (
        ('campaign-running', 'Campaign - Running'),
        ('campaign-stopped', 'Campaign - Stopped'),
    )),
    ('Done', (
        ('done-completed', 'Done - Completed'),
        ('done-incomplete', 'Done - Incomplete'),
        ('done-stopped', 'Done - Stopped'),
    )),
)

# Twitter handles, per language
TWITTER_HANDLES = {
    'nl': '1procentclub',
    'en': '1percentclub',
}

DEFAULT_TWITTER_HANDLE = TWITTER_HANDLES['nl']

# E-MAILS
CONTACT_EMAIL = 'contact@my-bluebottle-project.com'

# Registration
ACCOUNT_ACTIVATION_DAYS = 7
HTML_ACTIVATION_EMAIL = True

SEND_WELCOME_MAIL = False

THUMBNAIL_DEBUG = False
