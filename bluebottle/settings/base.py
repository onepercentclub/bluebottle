import datetime
import os
from collections import OrderedDict

from .admin_dashboard import *  # noqa
from django.utils.translation import gettext_lazy as _

import rules
from PIL import ImageFile

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

SUPPORT_EMAIL_ADDRESSES = []

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

FILE_UPLOAD_PERMISSIONS = 0o644

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
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
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'tenant_extras.context_processors.conf_settings',
                'tenant_extras.context_processors.tenant_properties'
            ],
        },
    },
]

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

MIDDLEWARE = (
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
    'axes.middleware.AxesMiddleware',
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
    'DEFAULT_THROTTLE_RATES': {
        'user': '10/hour'
    }
}

if not DEBUG:
    REST_FRAMEWORK['DEFAULT_METADATA_CLASS'] = None


JWT_AUTH = {
    'JWT_LEEWAY': 0,
    'JWT_VERIFY': True,
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_ALLOW_TOKEN_RENEWAL': True,
    'JWT_AUTH_HEADER_PREFIX': 'JWT',
    'JWT_GET_USER_SECRET_KEY': 'bluebottle.members.utils.get_jwt_secret',
    'JWT_PAYLOAD_HANDLER': 'bluebottle.members.utils.jwt_payload_handler',
}

# Time between attempts to refresh the jwt token automatically on standard request
# TODO: move this setting into the JWT_AUTH settings.
JWT_TOKEN_RENEWAL_DELTA = datetime.timedelta(minutes=30)
JWT_TOKEN_RENEWAL_LIMIT = datetime.timedelta(days=90)
JWT_EXPIRATION_DELTA = datetime.timedelta(days=7)

# List of paths to ignore for locale redirects
LOCALE_REDIRECT_IGNORE = ('/docs', '/go', '/api',
                          '/media', '/downloads', '/login-with',
                          '/surveys', '/token', '/jet')

SOCIAL_AUTH_STRATEGY = 'social.strategies.django_strategy.DjangoStrategy'
SOCIAL_AUTH_STORAGE = 'social_django.models.DjangoStorage'


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
    'axes.backends.AxesBackend',
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
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
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
    'bluebottle.auth.utils.refresh',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details',
    'bluebottle.auth.utils.set_language',
    'bluebottle.auth.utils.save_profile_picture',
    'bluebottle.auth.utils.get_extra_facebook_data',
)

AFOM_ENABLED = False

SHARED_APPS = (
    'bluebottle.clients',  # you must list the app where your tenant model resides in
    'tenant_schemas',
    'django_extensions',
    'django_admin_inline_paginator',
    'django_better_admin_arrayfield',

    # Django apps
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    'mapwidgets',

    # 3rd party apps
    'lockdown',
    'micawber.contrib.mcdjango',  # Embedding videos
    'tenant_extras',
    'localflavor',
    'corsheaders',
    'parler',
    'daterange_filter',
    'adminsortable',
    'solo',
    'django_filters',
    'multiselectfield',

    'djmoney.contrib.exchange',
)

TENANT_APPS = (
    'polymorphic',
    'social_django',
    'django.contrib.contenttypes',
    # Allow the Bluebottle common app to override the admin branding
    'bluebottle.common',
    'bluebottle.token_auth',

    'bluebottle.bluebottle_dashboard',
    'jet',
    'jet.dashboard',
    'rest_framework',

    'admin_tools',
    # 'admin_tools.theming',
    # 'admin_tools.menu',
    # 'admin_tools.dashboard',

    # Thumbnails
    'sorl.thumbnail',

    # FB Auth
    'bluebottle.auth',

    'bluebottle.fsm',
    'django.contrib.admin',
    'django.contrib.sites',
    'django.contrib.admindocs',
    'django.contrib.auth',

    'rest_framework.authtoken',
    'django_elasticsearch_dsl',

    'bluebottle.looker',
    'bluebottle.exports',

    'bluebottle.members',
    'bluebottle.projects',
    'bluebottle.organizations',
    'bluebottle.impact',

    'bluebottle.transitions',
    'bluebottle.files',
    'bluebottle.follow',
    'bluebottle.activities',
    'bluebottle.initiatives',
    'bluebottle.time_based',
    'bluebottle.collect',
    'bluebottle.deeds',
    'bluebottle.events',
    'bluebottle.assignments',
    'bluebottle.funding',
    'bluebottle.funding_pledge',
    'bluebottle.funding_stripe',
    'bluebottle.funding_vitepay',
    'bluebottle.funding_flutterwave',
    'bluebottle.funding_lipisha',
    'bluebottle.funding_telesom',
    'bluebottle.segments',
    'bluebottle.tasks',
    'bluebottle.payouts',
    'bluebottle.payouts_dorado',
    'bluebottle.surveys',
    'bluebottle.wallposts',
    'bluebottle.utils',
    'bluebottle.analytics',
    'bluebottle.categories',
    'bluebottle.contentplugins',
    'bluebottle.geo',
    'bluebottle.offices',
    'bluebottle.pages',
    'bluebottle.mails',
    'bluebottle.notifications',
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
    'taggit',

    'bluebottle.cms',

    'django.contrib.gis',
    'djmoney',
    'solo',
    'nested_inline',
    'permissions_widget',
    'django.forms',
    'axes',
    'captcha',
    'colorfield',
    'django_summernote',
)


INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

CSRF_USE_SESSIONS = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_AGE = 24 * 60 * 60

TENANT_MODEL = "clients.Client"
TENANT_PROPERTIES = "bluebottle.clients.properties"

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_ENGINE = 'bluebottle.clients.session_backends'

THUMBNAIL_DEBUG = False
THUMBNAIL_QUALITY = 85
THUMBNAIL_PRESERVE_FORMAT = True

DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(name)s %(module)s %(process)d %(thread)d %(message)s'
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
        'json': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(PROJECT_ROOT, 'logs', 'api-json.log'),
            'formatter': 'json',
            'when': 'midnight',
        },
        'syslog': {
            'level': 'INFO',
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'verbose',
            'facility': 'local0',
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
            'handlers': ['console', 'syslog'],
            'propagate': True,
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

IMAGE_ALLOWED_MIME_TYPES = (
    'image/png', 'image/jpeg', 'image/gif', 'image/svg+xml'
)
VIDEO_FILE_ALLOWED_MIME_TYPES = (
    'video/ogg', 'video/mp4', 'video/webm', 'video/3gpp',
    'video/x-msvideo', 'video/quicktime'
)
PRIVATE_FILE_ALLOWED_MIME_TYPES = (
    'image/png', 'image/jpeg', 'image/gif', 'image/tiff',
    'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/pdf', 'application/vnd.oasis.opendocument.text',
    'text/rtf'
)

EXPORTDB_EXPORT_CONF = {
    'models': OrderedDict([
        ('members.Member', {
            'fields': (
                ('id', 'User ID'),
                ('remote_id', 'Remote ID'),
                ('get_full_name', 'Name'),
                ('first_name', 'First Name'),
                ('last_name', 'Last Name'),
                ('email', 'Email'),
                ('location__name', _('Office location')),
                ('birthdate', 'Birthdate'),
                ('gender', 'Gender'),
                ('place__street', 'Street'),
                ('place__street_number', 'Number'),
                ('place__locality', 'City'),
                ('place__postal_code', 'Postal code'),
                ('place__country__name', 'Country'),
                ('date_joined', 'Date joined'),
                ('updated', 'Last update'),
            ),
            'resource_class': 'bluebottle.exports.resources.UserResource',
            'title': _('Users'),
        }),
        ('initiatives.Initiative', {
            'fields': (
                ('id', 'Initiative ID'),
                ('owner__id', 'User ID'),
                ('owner__remote_id', 'Remote ID'),
                ('owner__email', 'Email'),
                ('reviewer__id', 'Reviewer ID'),
                ('status', 'Status'),
                ('title', 'Title'),
                ('theme__name', 'Theme'),
                ('location', _('Office location')),
                ('location__group', 'Region'),
                ('place__locality', 'Location'),
                ('place__country__name', 'Country'),
                ('place__country__alpha2_code', 'Country Code'),
                ('pitch', 'Pitch'),
                ('story', 'Story'),
                ('image__file', 'Image'),

                ('created', 'Date created'),
                ('updated', 'Last update'),
            ),
            'resource_class': 'bluebottle.exports.resources.InitiativeResource',
            'title': _('Initiatives'),
        }),
        ('time_based.PeriodActivity', {
            'fields': (
                ('id', 'Task ID'),
                ('initiative__title', 'Initiative Title'),
                ('initiative__id', 'Initiative ID'),
                ('owner__id', 'User ID'),
                ('owner__remote_id', 'Remote ID'),
                ('owner__email', 'Email'),
                ('title', 'Title'),
                ('description', 'Description'),
                ('status', 'Status'),
                ('location__locality', 'Location'),
                ('location__country__name', 'Country'),
                ('location__country__alpha2_code', 'Country Code'),
                ('fallback_location', _('Office location')),

                ('expertise', 'Skill'),
                ('capacity', 'People needed'),
                ('duration', 'Time needed'),
                ('preparation', 'Preparation time'),
                ('start', 'Start'),
                ('deadline', 'Deadline'),

                ('created', 'Date created'),
                ('updated', 'Last update'),
            ),
            'resource_class': 'bluebottle.exports.resources.PeriodActivityResource',
            'title': _('Activities during a period'),
        }),
        ('time_based.PeriodParticipant', {
            'fields': (
                ('id', 'Participant ID'),
                ('activity__title', 'Activity Title'),
                ('activity__initiative__title', 'Initiative Title'),
                ('activity__id', 'Activity ID'),
                ('activity__status', 'Activity status'),
                ('user__id', 'User ID'),
                ('user__remote_id', 'Remote ID'),
                ('user__email', 'Email'),
                ('status', 'Status'),
            ),
            'resource_class': 'bluebottle.exports.resources.PeriodParticipantResource',
            'title': _('Participants over a period'),
        }),
        ('time_based.DateActivity', {
            'fields': (
                ('id', 'Task ID'),
                ('initiative__title', 'Initiative Title'),
                ('initiative__id', 'Initiative ID'),
                ('owner__id', 'User ID'),
                ('owner__remote_id', 'Remote ID'),
                ('owner__email', 'Email'),
                ('title', 'Title'),
                ('description', 'Description'),
                ('status', 'Status'),
                ('fallback_location', _('Office location')),

                ('expertise', 'Skill'),

                ('capacity', 'People needed'),
                ('created', 'Date created'),
                ('updated', 'Last update'),
            ),
            'resource_class': 'bluebottle.exports.resources.DateActivityResource',
            'title': _('Activities on a date'),
        }),

        ('time_based.DateActivitySlot', {
            'fields': (
                ('id', 'Slot ID'),
                ('activity__initiative__title', 'Initiative Title'),
                ('activity__initiative__id', 'Initiative ID'),
                ('activity__title', 'Activity Title'),
                ('activity__id', 'Activity ID'),

                ('status', 'Status'),

                ('location__locality', 'Location'),
                ('location__country__name', 'Country'),
                ('location__country__alpha2_code', 'Country Code'),

                ('start', 'Start'),
                ('duration', 'Duration'),
                ('capacity', 'People needed'),
            ),
            'resource_class': 'bluebottle.exports.resources.DateActivitySlotResource',
            'title': _('Activity slots'),
        }),
        ('time_based.DateParticipant', {
            'fields': (
                ('id', 'Participant ID'),
                ('activity__title', 'Activity Title'),
                ('activity__initiative__title', 'Initiative Title'),
                ('activity__id', 'Activity ID'),
                ('activity__status', 'Activity status'),
                ('user__id', 'User ID'),
                ('user__remote_id', 'Remote ID'),
                ('user__email', 'Email'),
                ('status', 'Status'),
            ),
            'resource_class': 'bluebottle.exports.resources.DateParticipantResource',
            'title': _('Participants on a date'),
        }),

        ('time_based.DateSlotParticipant', {
            'fields': (
                ('id', 'Slot Participant ID'),
                ('slot__id', 'Slot ID'),
                ('participant__activity__title', 'Activity Title'),
                ('participant__activity__initiative__title', 'Initiative Title'),
                ('participant__activity__id', 'Activity ID'),
                ('participant__activity__status', 'Activity status'),
                ('participant__id', 'Participant ID'),
                ('participant__status', 'Participant status'),
                ('participant__user__id', 'User ID'),
                ('participant__user__remote_id', 'Remote ID'),
                ('participant__user__email', 'Email'),
                ('status', 'Status'),
            ),
            'resource_class': 'bluebottle.exports.resources.SlotParticipantResource',
            'title': _('Slot participants'),
        }),
        ('time_based.TimeContribution', {
            'fields': (
                ('id', 'Contribution ID'),
                ('contributor__id', 'Participant ID'),
                ('contributor__activity__title', 'Activity Title'),
                ('contributor__activity__initiative__title', 'Initiative Title'),
                ('contributor__activity__id', 'Activity ID'),
                ('contributor__activity__status', 'Activity status'),
                ('contributor__user__id', 'User ID'),
                ('contributor__user__remote_id', 'Remote ID'),
                ('contributor__user__email', 'Email'),

                ('slot_participant__slot__id', 'Slot ID'),

                ('status', 'Status'),

                ('value', 'Time spent'),

                ('start', 'Start of contribution'),
                ('end', 'End of contribution'),
                ('created', 'Date registered'),
                ('updated', 'Last update'),
            ),
            'resource_class': 'bluebottle.exports.resources.TimeContributionResource',
            'title': _('Time contributions'),
        }),
        ('funding.Funding', {
            'fields': (
                ('id', 'Funding ID'),
                ('initiative__title', 'Initiative Title'),
                ('initiative__id', 'Initiative ID'),
                ('owner__id', 'User ID'),
                ('owner__remote_id', 'Remote ID'),
                ('owner__email', 'Email'),
                ('title', 'Title'),
                ('description', 'Description'),
                ('status', 'Status'),
                ('fallback_location', _('Office location')),

                ('target', 'Target'),
                ('amount_matching', 'Amount matching'),
                ('amount_donated', 'Amount donated'),
                ('deadline', 'Deadline'),

                ('created', 'created'),
                ('updated', 'Last update'),
            ),
            'resource_class': 'bluebottle.exports.resources.DateActivityResource',
            'title': _('Funding activities'),
        }),
        ('funding.Donor', {
            'fields': (
                ('id', 'Contributor ID'),
                ('activity__title', 'Activity Title'),
                ('activity__initiative__title', 'Initiative Title'),
                ('activity__id', 'Activity ID'),
                ('activity__status', 'Activity status'),
                ('user__id', 'User ID'),
                ('user__remote_id', 'Remote ID'),
                ('user__email', 'Email'),
                ('status', 'Status'),

                ('amount', 'Amount'),
                ('anonymous', 'Anonymous'),
                ('reward__name', 'Reward'),
                ('name', 'Name'),

                ('activity__funding__deadline', 'Activity date'),
                ('created', 'Donor date'),
                ('updated', 'Last update'),
            ),
            'resource_class': 'bluebottle.exports.resources.DonationResource',
            'title': _('Funding contributors'),
        }),
        ('deeds.Deed', {
            'fields': (
                ('id', 'Task ID'),
                ('initiative__title', 'Initiative Title'),
                ('initiative__id', 'Initiative ID'),
                ('owner__id', 'User ID'),
                ('owner__remote_id', 'Remote ID'),
                ('owner__email', 'Email'),
                ('title', 'Title'),
                ('description', 'Description'),
                ('status', 'Status'),
                ('start', 'Start'),
                ('end', 'End'),

                ('created', 'Date created'),
                ('updated', 'Last update'),
            ),
            'resource_class': 'bluebottle.exports.resources.DeedResource',
            'title': _('Deed activities'),
        }),
        ('deeds.DeedParticipant', {
            'fields': (
                ('id', 'Participant ID'),
                ('activity__title', 'Activity Title'),
                ('activity__initiative__title', 'Initiative Title'),
                ('activity__id', 'Activity ID'),
                ('activity__status', 'Activity status'),
                ('user__id', 'User ID'),
                ('user__remote_id', 'Remote ID'),
                ('user__email', 'Email'),
                ('status', 'Status'),
            ),
            'resource_class': 'bluebottle.exports.resources.DeedParticipantResource',
            'title': _('Deed participants'),
        }),
        ('activities.EffortContribution', {
            'fields': (
                ('id', 'Contribution ID'),
                ('contributor__id', 'Participant ID'),
                ('contributor__activity__title', 'Activity Title'),
                ('contributor__activity__initiative__title', 'Initiative Title'),
                ('contributor__activity__id', 'Activity ID'),
                ('contributor__activity__status', 'Activity status'),

                ('contributor__user__id', 'User ID'),
                ('contributor__user__remote_id', 'Remote ID'),
                ('contributor__user__email', 'Email'),

                ('status', 'Status'),
                ('contribution_type', 'Contribution type'),

                ('start', 'Start of contribution'),
                ('end', 'End of contribution'),
                ('created', 'Date registered'),
                ('updated', 'Last update'),
            ),
            'resource_class': 'bluebottle.exports.resources.EffortContributionResource',
            'title': _('Effort contributions'),
        }),

        ('collect.CollectActivity', {
            'fields': (
                ('id', 'Task ID'),
                ('initiative__title', 'Initiative Title'),
                ('initiative__id', 'Initiative ID'),
                ('owner__id', 'User ID'),
                ('owner__remote_id', 'Remote ID'),
                ('owner__email', 'Email'),
                ('title', 'Title'),
                ('description', 'Description'),
                ('status', 'Status'),
                ('start', 'Start'),
                ('end', 'End'),

                ('created', 'Date created'),
                ('updated', 'Last update'),
            ),
            'resource_class': 'bluebottle.exports.resources.CollectActivityResource',
            'title': _('Collection campaigns'),
        }),
        ('collect.CollectContributor', {
            'fields': (
                ('id', 'Contributor ID'),
                ('activity__title', 'Activity Title'),
                ('activity__initiative__title', 'Initiative Title'),
                ('activity__id', 'Activity ID'),
                ('activity__status', 'Activity status'),
                ('user__id', 'User ID'),
                ('user__remote_id', 'Remote ID'),
                ('user__email', 'Email'),
                ('status', 'Status'),
            ),
            'resource_class': 'bluebottle.exports.resources.CollectContributorResource',
            'title': _('Collection contributors'),
        }),
    ])
}

EXPORTDB_CONFIRM_FORM = 'bluebottle.exports.forms.ExportDBForm'
EXPORTDB_EXPORT_ROOT = os.path.join(MEDIA_ROOT, '%s', 'private', 'exports')
EXPORTDB_PERMISSION = rules.is_group_member('Staff') | rules.is_superuser
EXPORTDB_USE_CELERY = True
EXPORTDB_EXPORT_MEDIA_URL = os.path.join(MEDIA_URL, 'private/exports')

# maximum delta between from/to date for exports
EXPORT_MAX_DAYS = 365 * 20

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
BASE_CURRENCY = 'USD'

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

SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id,name,email,first_name,last_name,link',  # needed starting from protocol v2.4
}

SURVEYGIZMO_API_TOKEN = ''
SURVEYGIZMO_API_SECRET = ''

GEOPOSITION_GOOGLE_MAPS_API_KEY = ''
STATIC_MAPS_API_KEY = ''
STATIC_MAPS_API_SECRET = ''

# django money settings
OPEN_EXCHANGE_RATES_APP_ID = 'c2cedc60485a48efa65631d5230c23e1'
RATES_CACHE_TIMEOUT = 60 * 60 * 24

AUTO_CONVERT_MONEY = False

LOCKDOWN_URL_EXCEPTIONS = [
    r'^/api/funding/vitepay/webhook/'
    r'^/api/scim/v2/'
]

# THUMBNAIL_ENGINE = 'sorl_watermarker.engines.pil_engine.Engine'
# THUMBNAIL_WATERMARK_ALWAYS = False

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

JSON_API_FORMAT_FIELD_NAMES = 'dasherize'
JSON_API_UNIFORM_EXCEPTIONS = True

# Don't show url warnings
SILENCED_SYSTEM_CHECKS = ['urls.W002', 'captcha.recaptcha_test_key_error']

AXES_LOCKOUT_URL = '/admin/locked/'
AXES_FAILURE_LIMIT = 10
AXES_COOLOFF_TIME = datetime.timedelta(minutes=10)
AXES_META_PRECEDENCE_ORDER = [
    'HTTP_X_FORWARDED_FOR',
    'REMOTE_ADDR',
]
AXES_NUM_PROXIES = 1
AXES_USERNAME_FORM_FIELD = 'email'

RECAPTCHA_PRIVATE_KEY = "6LdJvSUTAAAAALYWDHKOyhRkSt8MOAOW9ScSPcjS"
RECAPTCHA_PUBLIC_KEY = "6LdJvSUTAAAAAMLwr45uU-qD7IScJM3US0J_RZQM"
USE_X_FORWARDED_HOST = True

ORIGINAL_BACKEND = 'django.contrib.gis.db.backends.postgis'

# Socket is not configured. Lets guess.
if os.path.exists('/var/run/clamd.scan/'):
    # Fedora, CentOS
    CLAMD_SOCKET = '/var/run/clamd.scan/clamd.sock'
else:
    # This is default for Ubuntu, Debian based distributions
    CLAMD_SOCKET = '/var/run/clamav/clamd.ctl'

MATCHING_DISTANCE = 50
