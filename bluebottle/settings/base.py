import os
import datetime
from collections import OrderedDict
import rules
from PIL import ImageFile

from .payments import *  # noqa
from .admin_dashboard import *  # noqa

BASE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir))
PROJECT_ROOT = BASE_DIR

DEBUG = True
COMPRESS_ENABLED = False
COMPRESS_TEMPLATES = False

INCLUDE_TEST_MODELS = False

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

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

TENANT_BASE = os.path.join(PROJECT_ROOT, 'static', 'media')

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
    os.path.join(BASE_DIR, 'bluebottle/static'),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    # You can also name this tuple like: ('css', '/path/to/css')
)

ROOT_URLCONF = 'bluebottle.urls'

MULTI_TENANT_DIR = os.path.join(PROJECT_ROOT, 'tenants')

COMPRESS_OUTPUT_DIR = 'compressed'

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'tenant_extras.staticfiles_finders.TenantStaticFilesFinder'
)

# List of callables that know how to import templates from various sources.

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'debug': DEBUG,
            'loaders': [
                'tenant_extras.template_loaders.FilesystemLoader',
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'django.template.loaders.eggs.Loader',
                'admin_tools.template_loaders.Loader',
            ],
            'context_processors': [
                'bluebottle.clients.context_processors.tenant',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'social.apps.django_app.context_processors.backends',
                'social.apps.django_app.context_processors.login_redirect',
                'tenant_extras.context_processors.conf_settings',
                'tenant_extras.context_processors.tenant_properties'
            ],
        },
    },
]

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'bluebottle.bluebottle_drf2.middleware.MethodOverrideMiddleware',
    'tenant_schemas.middleware.TenantMiddleware',
    'bluebottle.clients.middleware.MediaMiddleware',
    'tenant_extras.middleware.TenantLocaleMiddleware',
    'bluebottle.redirects.middleware.RedirectFallbackMiddleware',
    'bluebottle.auth.middleware.UserJwtTokenMiddleware',
    'bluebottle.utils.middleware.SubDomainSessionMiddleware',
    'bluebottle.utils.middleware.APILanguageMiddleware',
    'bluebottle.auth.middleware.AdminOnlySessionMiddleware',
    'bluebottle.auth.middleware.AdminOnlyCsrf',
    'bluebottle.auth.middleware.AdminOnlyAuthenticationMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'bluebottle.auth.middleware.LockdownMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_tools.middlewares.ThreadLocal.ThreadLocalMiddleware',
    'bluebottle.auth.middleware.SlidingJwtTokenMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'bluebottle.auth.middleware.LogAuthFailureMiddleWare',
)

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication'
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'bluebottle.utils.permissions.TenantConditionalOpenClose',
    ),
}

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=7),
    'JWT_LEEWAY': 0,
    'JWT_VERIFY': True,
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_ALLOW_TOKEN_RENEWAL': True,
    # After the renewal limit it isn't possible to request a token refresh
    # => time token first created + renewal limit.
    'JWT_TOKEN_RENEWAL_LIMIT': datetime.timedelta(days=90),

    # Override the JWT token handlers, use tenant aware ones.
    'JWT_ENCODE_HANDLER':
        'tenant_extras.jwt_utils.jwt_encode_handler',

    'JWT_DECODE_HANDLER':
        'tenant_extras.jwt_utils.jwt_decode_handler',
}

# Time between attempts to refresh the jwt token automatically on standard request
# TODO: move this setting into the JWT_AUTH settings.
JWT_TOKEN_RENEWAL_DELTA = datetime.timedelta(minutes=30)

# List of paths to ignore for locale redirects
LOCALE_REDIRECT_IGNORE = ('/docs', '/go', '/api', '/payments_docdata',
                          '/payments_mock', '/payments_interswitch',
                          '/payments_vitepay', '/payments_flutterwave',
                          '/payments_lipisha', '/payments_beyonic',
                          '/payments_stripe', '/payouts_stripe',
                          '/media', '/downloads',
                          '/surveys', '/token', '/jet')

SOCIAL_AUTH_STRATEGY = 'social.strategies.django_strategy.DjangoStrategy'
SOCIAL_AUTH_STORAGE = 'social.apps.django_app.default.models.DjangoStorage'


PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
    'hashers_passlib.phpass',
)

AUTHENTICATION_BACKENDS = (
    'bluebottle.social.backends.NoStateFacebookOAuth2',
    'social.backends.facebook.FacebookAppOAuth2',
    'django.contrib.auth.backends.ModelBackend',
    'bluebottle.utils.backends.AnonymousAuthenticationBackend'
)


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
]

SOCIAL_AUTH_PIPELINE = (
    'bluebottle.auth.utils.user_from_request',
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',
    'bluebottle.auth.utils.fallback_email',
    'social.pipeline.user.get_username',
    'social.pipeline.social_auth.associate_by_email',
    'social.pipeline.user.create_user',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details',
    'bluebottle.auth.utils.refresh',
    'bluebottle.auth.utils.set_language',
    'bluebottle.auth.utils.save_profile_picture',
    'bluebottle.auth.utils.get_extra_facebook_data',
)

AFOM_ENABLED = False

SHARED_APPS = (
    'tenant_schemas',
    'bluebottle.clients',  # you must list the app where your tenant model resides in

    # Django apps
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    # 3rd party apps
    'lockdown',
    'django_extensions',
    'raven.contrib.django',
    'djcelery',
    'micawber.contrib.mcdjango',  # Embedding videos
    'rest_framework',
    'loginas',
    'geoposition',
    'tenant_extras',
    'localflavor',
    'filetransfers',
    'corsheaders',
    'djmoney_rates',
    'parler',
    'daterange_filter',
    'adminsortable',
    'django_summernote',
    'django_singleton_admin',
    'django_filters'
)

TENANT_APPS = (
    'polymorphic',
    'modeltranslation',

    'social.apps.django_app.default',
    'django.contrib.contenttypes',
    # Allow the Bluebottle common app to override the admin branding
    'bluebottle.common',
    'bluebottle.token_auth',

    'bluebottle.bluebottle_dashboard',
    'jet',
    'jet.dashboard',

    'admin_tools',
    # 'admin_tools.theming',
    # 'admin_tools.menu',
    # 'admin_tools.dashboard',

    # Thumbnails
    'sorl.thumbnail',

    # FB Auth
    'bluebottle.auth',

    'django.contrib.admin',
    'django.contrib.sites',
    'django.contrib.admindocs',
    'django.contrib.auth',

    'bb_salesforce',

    # Widget
    'bluebottle.widget',

    'rest_framework.authtoken',
    'django_elasticsearch_dsl',

    'bluebottle.looker',

    'bluebottle.members',
    'bluebottle.projects',
    'bluebottle.organizations',

    'bluebottle.tasks',
    'bluebottle.homepage',
    'bluebottle.payouts',
    'bluebottle.payouts_dorado',
    'bluebottle.surveys',
    'bluebottle.wallposts',
    'bluebottle.utils',
    'bluebottle.analytics',
    'bluebottle.categories',
    'bluebottle.contentplugins',
    'bluebottle.contact',
    'bluebottle.geo',
    'bluebottle.pages',
    'bluebottle.mails',
    'bluebottle.news',
    'bluebottle.slides',
    'bluebottle.quotes',
    'bluebottle.payments',
    'bluebottle.payments_beyonic',
    'bluebottle.payments_docdata',
    'bluebottle.payments_external',
    'bluebottle.payments_flutterwave',
    'bluebottle.payments_interswitch',
    'bluebottle.payments_lipisha',
    'bluebottle.payments_logger',
    'bluebottle.payments_pledge',
    'bluebottle.payments_stripe',
    'bluebottle.payments_telesom',
    'bluebottle.payments_vitepay',
    'bluebottle.payments_voucher',
    'bluebottle.redirects',
    'bluebottle.statistics',
    'bluebottle.suggestions',
    'bluebottle.terms',
    'bluebottle.votes',
    'bluebottle.social',
    'bluebottle.rewards',
    'bluebottle.scim',

    # Custom dashboard
    # 'fluent_dashboard',

    # Bluebottle apps with abstract models
    'bluebottle.bb_accounts',
    'bluebottle.bb_projects',
    'bluebottle.bb_tasks',
    'bluebottle.bb_fundraisers',
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
    'exportdb',
    'django.contrib.humanize',
    'django_tools',
    'taggit',

    'bluebottle.cms',

    # Note: Fixes the incorrect formatting of money values in the back-office
    # https://github.com/django-money/django-money/issues/232
    'djmoney',
    'django_singleton_admin',
    'nested_inline',
    'permissions_widget'
)


INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

TENANT_MODEL = "clients.Client"
TENANT_PROPERTIES = "bluebottle.clients.properties"

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

THUMBNAIL_DEBUG = False
THUMBNAIL_QUALITY = 85
THUMBNAIL_DUMMY = True
THUMBNAIL_PRESERVE_FORMAT = True

DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(name) %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        },
        'json': {
            '()': 'bluebottle.utils.formatters.JsonFormatter'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
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
        },
        'json': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(PROJECT_ROOT, 'logs', 'api-json.log'),
            'formatter': 'json',
            'when': 'midnight',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(PROJECT_ROOT, 'logs', 'api.log'),
            'formatter': 'simple',
            'when': 'midnight',
        },
        'default': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'propagate': True,
            'level': 'ERROR',
        },
        'bluebottle': {
            'handlers': ['console', 'file'],
            'propagate': True,
            'level': 'INFO',
        },
        'bluebottle.salesforce': {
            'handlers': ['mail_admins'],
            'propagate': True,
            'level': 'ERROR',
        },
        'payments.payment': {
            'handlers': ['mail_admins', 'payment_logs', 'sentry'],
            'propagate': False,
            'level': 'INFO',
        },
    }
}

# Custom User model
AUTH_USER_MODEL = 'members.Member'

SOCIAL_AUTH_USER_FIELDS = ('username', 'email', 'first_name', 'last_name',)
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email', ]
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_USER_MODEL = 'members.Member'
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'user_friends', 'public_profile', 'user_birthday']
SOCIAL_AUTH_FACEBOOK_EXTRA_DATA = [('birthday', 'birthday')]

# Default Client properties
DONATIONS_ENABLED = True

# Analytics Service
ANALYTICS_ENABLED = False
ANALYTICS_BACKENDS = {
    'influxdb': {
        'handler_class': 'bluebottle.analytics.backends.InfluxExporter',
        'host': 'localhost',
        'port': 8086,
        'username': '',
        'password': '',
        'database': 'platform_v1',
        'measurement': 'saas',
        'ssl': True
    },
    'file': {
        'handler_class': 'bluebottle.analytics.backends.FileExporter',
        'base_dir': os.path.join(PROJECT_ROOT, 'analytics'),
        'measurement': 'saas',
    }
}

ANALYTICS_FRONTEND = ''
ANALYTICS_BACKOFFICE_ENABLED = True
REPORTING_BACKOFFICE_ENABLED = False
PARTICIPATION_BACKOFFICE_ENABLED = False
REPORT_SQL_DIR = ''

# PROJECT_TYPES = ['sourcing', 'funding'] or ['sourcing'] or ['funding']
# PROJECT_CREATE_FLOW = 'combined' or 'choice'
# If only one project type is set then project create should be set to 'combined'
PROJECT_CREATE_TYPES = ['funding']
PROJECT_CREATE_FLOW = 'combined'
PROJECT_CONTACT_TYPES = [
    'organization',
]
PROJECT_CONTACT_METHOD = 'mail'

# For building frontend code
BB_APPS = []

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
HTML_ACTIVATION_EMAIL = False

SEND_WELCOME_MAIL = True

EMAIL_BACKEND = 'bluebottle.utils.email_backend.TestMailBackend'

# and provide a default (without it django-rest-framework-jwt will default
# to SECRET_KEY. Even better, provide one in a client's properties.py file
TENANT_JWT_SECRET = 'global-tenant-secret'

# email properties
TENANT_MAIL_PROPERTIES = {
    'logo': '',
    'address': '',
    'sender': '',
    'footer': '',
    'website': '',
}

CLOSED_SITE = False
PARTNER_LOGIN = False

EXPOSED_TENANT_PROPERTIES = [
    'mixpanel', 'analytics', 'maps_api_key', 'git_commit',
    'social_auth_facebook_key', 'date_format', 'bb_apps', 'donation_amounts',
    'facebook_sharing_reviewed', 'project_create_flow', 'project_create_types',
    'project_contact_types', 'project_contact_method', 'closed_site',
    'partner_login', 'share_options', 'sso_url', 'project_suggestions',
    'readOnlyFields', 'search_options', 'tasks'
]

DEFAULT_FILE_STORAGE = 'bluebottle.utils.storage.TenantFileSystemStorage'

PROJECT_PAYOUT_FEES = {
    'beneath_threshold': 1,
    'fully_funded': .05,
    'not_fully_funded': .05
}

LIVE_PAYMENTS_ENABLED = False
MINIMAL_PAYOUT_AMOUNT = 20

CELERY_MAIL = False
SEND_MAIL = False

DJANGO_WYSIWYG_FLAVOR = "tinymce_advanced"

# Sometimes images crash projects
# Error: Exception Value: image file is truncated (26 bytes not processed)
# This fixes it
# TODO: properly investigate

ImageFile.LOAD_TRUNCATED_IMAGES = True

IMAGE_ALLOWED_MIME_TYPES = ('image/png', 'image/jpeg', 'image/gif', 'image/svg+xml')

EXPORTDB_EXPORT_CONF = {
    'models': OrderedDict([
        (AUTH_USER_MODEL, {
            'fields': (
                ('id', 'User ID'),
                ('remote_id', 'Remote ID'),
                ('get_full_name', 'Name'),
                ('first_name', 'First Name'),
                ('last_name', 'Last Name'),
                ('email', 'Email'),
                ('location__name', 'Location'),
                ('project_count', 'Projects initiated'),
                ('projects_supported', 'Projects supported'),
                ('funding', 'Funding'),
                ('sourcing', 'Sourcing'),
                ('date_joined', 'Date joined'),
                ('updated', 'Last update'),
                ('address__line1', 'Address Line 1'),
                ('address__line2', 'Address Line 2'),
                ('address__city', 'City'),
                ('state', 'State'),
                ('address__country', 'Country'),
                ('address__postal_code', 'Postal Code'),
            ),
            'resource_class': 'bluebottle.exports.resources.UserResource',
            'title': 'Members',
        }),
        ('projects.Project', {
            'fields': (
                ('id', 'Project ID'),
                ('owner__id', 'User ID'),
                ('owner__remote_id', 'Remote ID'),
                ('reviewer__id', 'Reviewer ID'),
                ('status__name', 'Status'),
                ('title', 'Title'),
                ('owner__email', 'Email'),
                ('location', 'Location'),
                ('location__group', 'Region'),
                ('region', 'Region'),
                ('theme', 'Theme'),
                ('supporters', 'Supporters'),
                ('funding', 'Funding'),
                ('sourcing', 'Sourcing'),
                ('amount_asked', 'Amount asked'),
                ('amount_donated', 'Amount raised'),
                ('amount_extra', 'Amount matched'),
                ('task_count', 'Task Count'),
                ('has_survey', 'Has Survey'),
                ('realized_task_count', 'Realized Task Count'),
                ('time_spent', 'Time Spent'),
                ('from_suggestion', 'Submitted Suggestion'),
                ('vote_count', 'Vote Counts'),
                ('created', 'Date created'),
                ('deadline', 'Deadline'),
                ('updated', 'Last update'),
                ('date_submitted', 'Date Submitted'),
                ('campaign_started', 'Campaign Started'),
                ('campaign_ended', 'Campaign Ended'),
                ('campaign_funded', 'Campaign Funded'),
                ('organization__name', 'Organization'),
                ('account_holder_name', 'Account Holder Name'),
                ('account_holder_address', 'Account Holder Address'),
                ('account_holder_postal_code', 'Account Holder Postal Code'),
                ('account_holder_city', 'Account Holder City'),
                ('account_holder_country', 'Account Holder Country'),
                ('account_number', 'Account Number'),
                ('account_details', 'Account Details'),
                ('account_bank_country', 'Account Bank Country'),
            ),
            'resource_class': 'bluebottle.exports.resources.ProjectResource',
            'title': 'Projects',
        }),
        ('tasks.Task', {
            'fields': (
                ('project__id', 'Project ID'),
                ('id', 'Task ID'),
                ('author__id', 'User ID'),
                ('author__remote_id', 'Remote ID'),
                ('get_status_display', 'Status'),
                ('title', 'Title'),
                ('project__title', 'Project Title'),
                ('author__email', 'Email'),
                ('location', 'Task location'),
                ('location__group', 'Task Region'),
                ('type', 'Type'),
                ('skill', 'Skill Needed'),
                ('people_needed', 'People needed'),
                ('time_needed', 'Time needed'),
                ('people_applied', 'People applied'),
                ('time_spent', 'Time Spent'),
                ('date_realized', 'Date realized'),
                ('created', 'Date created'),
                ('updated', 'Last update'),
            ),
            'resource_class': 'bluebottle.exports.resources.TaskResource',
            'title': 'Tasks',
        }),
        ('donations.Donation', {
            'fields': (
                ('order__user__id', 'User ID'),
                ('order__user__remote_id', 'Remote ID'),
                ('project__id', 'Project ID'),
                ('fundraiser__id', 'Fundraiser ID'),
                ('order_id', 'Order ID'),
                ('user__get_full_name', 'Name'),
                ('order__user__email', 'Email'),
                ('order__user__location', 'Location'),
                ('order__user__location__group', 'Region'),
                ('status', 'Status'),
                ('amount', 'Amount'),
                ('created', 'Date'),
            ),
            'resource_class': 'bluebottle.exports.resources.DonationResource',
            'title': 'Supporters (Funding)',
        }),
        ('tasks.TaskMember', {
            'fields': (
                ('member__id', 'User ID'),
                ('member__remote_id', 'Remote ID'),
                ('task__project__id', 'Project ID'),
                ('task__project__location', 'Project Location'),
                ('task__project__location__group', 'Project Region'),
                ('task__id', 'Task ID'),
                ('member__get_full_name', 'Name'),
                ('member__email', 'Email'),
                ('member__location', 'Location'),
                ('member__location__group', 'Region'),
                ('get_status_display', 'Status'),
                ('task__time_needed', 'Time pledged'),
                ('time_spent', 'Time Spent'),
                ('externals', 'Partners'),
                ('created', 'Date'),
            ),
            'resource_class': 'bluebottle.exports.resources.TaskMemberResource',
            'title': 'Supporters (Sourcing)',
        }),
    ])
}
EXPORTDB_CONFIRM_FORM = 'bluebottle.exports.forms.ExportDBForm'
EXPORTDB_EXPORT_ROOT = os.path.join(MEDIA_ROOT, '%s', 'exports')
EXPORTDB_PERMISSION = rules.is_group_member('Staff') | rules.is_superuser

# maximum delta between from/to date for exports
EXPORT_MAX_DAYS = 366

TOKEN_AUTH_SETTINGS = 'bluebottle.clients.properties'

# FIXME: When caching is made tenant aware, re-enable fluent caching
FLUENT_CONTENTS_CACHE_OUTPUT = False

CACHE_MIDDLEWARE_SECONDS = 0

# Amounts shown in donation modal
DONATION_AMOUNTS = {
    'EUR': (25, 50, 75, 100),
    'USD': (20, 50, 100, 200),
    'NGN': (2000, 5000, 10000, 25000),
    'XOF': (500, 1000, 2000, 5000),
}

DEFAULT_CURRENCY = 'EUR'

# By default we do not show suggestion on the start-project page
PROJECT_SUGGESTIONS = False

# Social share options in project/fundraiser detail
SHARE_OPTIONS = {
    'twitter': True,
    'facebook': True,
    'linkedin': False,
    'embedded': False,
    'link': False,
    'flyer': False
}

SHOW_DONATION_AMOUNTS = True

# Salesforce connection settings
SALESFORCE_QUERY_TIMEOUT = 15
REQUESTS_MAX_RETRIES = 0
SF_LAZY_CONNECT = True

SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id,name,email,first_name,last_name,link',  # needed starting from protocol v2.4
}

SURVEYGIZMO_API_TOKEN = ''
SURVEYGIZMO_API_SECRET = ''

GEOPOSITION_GOOGLE_MAPS_API_KEY = ''

DJANGO_MONEY_RATES = {
    'DEFAULT_BACKEND': 'djmoney_rates.backends.OpenExchangeBackend',
    'OPENEXCHANGE_URL': 'http://openexchangerates.org/api/latest.json',
    'OPENEXCHANGE_APP_ID': '3e53678e72c140b4857dc5bb1deb59dc',
    'OPENEXCHANGE_BASE_CURRENCY': 'USD',
}
AUTO_CONVERT_MONEY = False

LOCKDOWN_URL_EXCEPTIONS = [r'^/payments_vitepay/status_update/']
THUMBNAIL_ENGINE = 'sorl_watermarker.engines.pil_engine.Engine'
THUMBNAIL_WATERMARK_ALWAYS = False

REMINDER_MAIL_DELAY = 60 * 24 * 3  # Three days

SEARCH_OPTIONS = {
    'filters': {
        'projects': [
            {
                'name': 'status'
            },
            {
                'name': 'location'
            },
            {
                'name': 'theme'
            }
        ]
    }
}

TASKS = {
    'cv_upload': 'disabled',  # allowed, required or disabled
    'accepting': 'manual',
    'plus_one': False,
    'show_accepting': True
}

ENABLE_REFUNDS = False


def static_url(url):
    return os.path.join(STATIC_URL, url)


SUMMERNOTE_CONFIG = {
    # Using SummernoteWidget - iframe mode
    'toolbar': [
        ['style', ['style']],
        ['style', ['bold', 'italic', 'underline', 'clear']],
        ['para', ['ul', 'ol']],
        ['insert', ['link', 'picture']],
        ['view', ['codeview']],
    ],
    'disable_upload': False,
    'attachment_model': 'projects.ProjectImage',
    'attachment_upload_to': 'project_images/',
    'summernote': {
        'disableResizeImage': True
    },
    'default_css': (
        static_url('rest_framework/css/bootstrap.min.css'),
        static_url('django_summernote/summernote.css'),
        static_url('django_summernote/django_summernote.css'),
    ),
    'default_js': (
        static_url('admin/js/vendor/jquery/jquery.min.js'),
        static_url('rest_framework/js/bootstrap.min.js'),
        static_url('django_summernote/jquery.ui.widget.js'),
        static_url('django_summernote/jquery.iframe-transport.js'),
        static_url('django_summernote/jquery.fileupload.js'),
        static_url('django_summernote/summernote.min.js'),
        static_url('django_summernote/ResizeSensor.js'),
    ),

}

HOMEPAGE = {}
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'localhost:9200'
    },
}

LOGOUT_REDIRECT_URL = 'admin:index'
LOGIN_REDIRECT_URL = 'admin:index'

TINYMCE_INCLUDE_JQUERY = False

LOOKER_SESSION_LENGTH = 60 * 60
TOKEN_LOGIN_TIMEOUT = 30
