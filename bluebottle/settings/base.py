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
    ("app", os.path.join(PROJECT_ROOT, 'frontend', 'app')),
    ("vendor", os.path.join(PROJECT_ROOT, 'frontend', 'static', 'vendor')),
    ("css", os.path.join(PROJECT_ROOT, 'frontend', 'static', 'css')),
    ("images", os.path.join(PROJECT_ROOT, 'frontend', 'static', 'images')),
    ("fonts", os.path.join(PROJECT_ROOT, 'frontend', 'static', 'fonts'))
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
    (os.path.join(PROJECT_ROOT, 'frontend', 'app', 'templates'))
)

MIDDLEWARE_CLASSES = (
    'tenant_schemas.middleware.TenantMiddleware',
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
    )
}

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(hours=12)
}

JWT_TOKEN_RENEWAL_DELTA = datetime.timedelta(minutes=30)


SHARED_APPS = (
    'bluebottle.clients', # you must list the app where your tenant model resides in

    # Django apps
    'south',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd party apps
    'django_extensions',
    'django_extensions.tests',
    'raven.contrib.django.raven_compat',
    'djcelery',
    'compressor',
    'sorl.thumbnail',
    'taggit',
    'taggit_autocomplete_modified',
    'micawber.contrib.mcdjango',  # Embedding videos
    'templatetag_handlebars',
    'rest_framework',
    'filetransfers',
    'loginas',
)

TENANT_APPS = (
    'south',
    'polymorphic',

    #'social_auth',
    'social.apps.django_app.default',

    # Custom dashboard
    'fluent_dashboard',

    'admin_tools',
    'admin_tools.theming',
    'admin_tools.menu',
    'admin_tools.dashboard',

    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',

    # FB Auth
    'bluebottle.auth',

    #Widget
    'bluebottle.widget',

    'rest_framework.authtoken',

    # Newly moved BB apps
    'bluebottle.members',
    'bluebottle.projects',
    'bluebottle.partners',
    'bluebottle.organizations',
    'bluebottle.tasks',
    'bluebottle.hbtemplates',
    'bluebottle.bluebottle_dashboard',
    'bluebottle.statistics',
    'bluebottle.homepage',
    'bluebottle.recurring_donations',
    'bluebottle.payouts',
    'bluebottle.bluebottle_salesforce',

    # Plain Bluebottle apps
    'bluebottle.wallposts',
    'bluebottle.utils',
    'bluebottle.common',
    'bluebottle.contentplugins',
    'bluebottle.contact',
    'bluebottle.geo',
    'bluebottle.pages',
    'bluebottle.news',
    'bluebottle.slides',
    'bluebottle.quotes',
    'bluebottle.payments',
    'bluebottle.payments_docdata',
    'bluebottle.payments_logger',
    'bluebottle.payments_voucher',
    'bluebottle.redirects',

    # Bluebottle apps with abstract models
    'bluebottle.bb_accounts',
    'bluebottle.bb_organizations',
    'bluebottle.bb_projects',
    'bluebottle.bb_tasks',
    'bluebottle.bb_fundraisers',
    'bluebottle.bb_donations',
    'bluebottle.bb_orders',
    'bluebottle.bb_payouts',
    'bluebottle.bb_follow',

    # Basic Bb implementations
    'bluebottle.fundraisers',
    'bluebottle.donations',
    'bluebottle.orders',

    # CMS page contents
    'fluent_contents',
    'fluent_contents.plugins.text',
    'fluent_contents.plugins.oembeditem',
    'fluent_contents.plugins.rawhtml',
    'django_wysiwyg',
    'tinymce',
    'django.contrib.humanize',
    'django_tools',
)

INSTALLED_APPS = TENANT_APPS + SHARED_APPS + ('tenant_schemas',)

TENANT_MODEL = "clients.Client"

SOUTH_DATABASE_ADAPTERS = {
    'default': 'south.db.postgresql_psycopg2',
}

SOUTH_MIGRATION_MODULES = {
    'taggit': 'taggit.south_migrations',
}

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
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

# Custom User model
AUTH_USER_MODEL = 'members.Member'

PROJECTS_PROJECT_MODEL = 'projects.Project'
PROJECTS_PHASELOG_MODEL = 'projects.ProjectPhaseLog'

FUNDRAISERS_FUNDRAISER_MODEL = 'fundraisers.Fundraiser'

TASKS_TASK_MODEL = 'tasks.Task'
TASKS_SKILL_MODEL = 'tasks.Skill'
TASKS_TASKMEMBER_MODEL = 'tasks.TaskMember'
TASKS_TASKFILE_MODEL = 'tasks.TaskFile'

ORGANIZATIONS_ORGANIZATION_MODEL = 'organizations.Organization'
ORGANIZATIONS_DOCUMENT_MODEL = 'organizations.OrganizationDocument'
ORGANIZATIONS_MEMBER_MODEL = 'organizations.OrganizationMember'

ORDERS_ORDER_MODEL = 'orders.Order'
DONATIONS_DONATION_MODEL = 'donations.Donation'

PAYOUTS_PROJECTPAYOUT_MODEL = 'payouts.ProjectPayout'
PAYOUTS_ORGANIZATIONPAYOUT_MODEL = 'payouts.OrganizationPayout'


# Default Client properties
RECURRING_DONATIONS_ENABLED = False
DONATIONS_ENABLED = True


# For building frontend code
BB_APPS = ['wallposts', 'utils', 'contacts', 'geo', 'pages', 'news', 'slides', 'quotes',
           'payments', 'payments-docdata', 'payments-voucher', 'payments-mock', 'members', 'organizations',
           'projects', 'tasks', 'fundraisers', 'donations', 'orders',
           'homepage', 'recurring-donations', 'partners']

MINIMAL_PAYOUT_AMOUNT = 21.00
VAT_RATE = '0.21'

# Required for handlebars_template to work properly
USE_EMBER_STYLE_ATTRS = True

# Twitter handles, per language
TWITTER_HANDLES = {
    'nl': '1procentclub',
    'en': '1percentclub',
}

DEFAULT_TWITTER_HANDLE = TWITTER_HANDLES['nl']

# Used when creating default payment address
DEFAULT_COUNTRY_CODE = 'NL'

# E-MAILS
CONTACT_EMAIL = 'contact@my-bluebottle-project.com'

# Registration
ACCOUNT_ACTIVATION_DAYS = 7
HTML_ACTIVATION_EMAIL = True

SEND_WELCOME_MAIL = False

TENANT_MAIL_PROPERTIES = {}

TENANT_BASE = os.path.join(PROJECT_ROOT, 'static', 'media')

PROJECT_PAYOUT_FEES = {
    'beneath_threshold': 1,
    'fully_funded': .05,
    'not_fully_funded': .05
}

EXPOSED_TENANT_PROPERTIES = ['mixpanel', 'analytics', 'maps_api_key', 'git_commit', \
                             'debug', 'compress_templates', 'facebook_auth_id', 'installed_apps', \
                             'bb_apps', ]

MIXPANEL = ''
MAPS_API_KEY = ''
ANALYTICS = ''
GIT_COMMIT = ''
DEBUG = True
COMPRESS_TEMPLATES = False
FACEBOOK_AUTH_ID = ''
