from django.conf import global_settings
import os

SITE_ID = 1
TIME_ZONE = 'Europe/Amsterdam'

PROJECT_ROOT = os.path.join(os.path.dirname(__file__))

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'bluebottle', 'test_files', 'media')

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'bluebottle', 'test_files', 'assets')

STATICI18N_ROOT = os.path.join(PROJECT_ROOT, 'bluebottle', 'test_files', 'global')

STATICFILES_DIRS = (
    (os.path.join(PROJECT_ROOT, 'bluebottle', 'test_files', 'global')),
)


STATIC_URL = '/static/assets/'
MEDIA_URL = '/static/media/'

COMPRESS_ENABLED = False # = True: causes tests to be failing for some reason

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
    # django-compressor staticfiles
    'compressor.finders.CompressorFinder',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': os.path.join(PROJECT_ROOT, 'bluebottle', 'test_files', 'test.db'),
        'NAME': ':memory:',
    }
}

SECRET_KEY = '$311#0^-72hr(uanah5)+bvl4)rzc*x1&amp;b)6&amp;fajqv_ae6v#zy'


INSTALLED_APPS = (
    # Django apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    #3rp party apps
    'compressor',
    'registration',
    'rest_framework',
    #'social_auth',
    'south',
    'taggit',
    'templatetag_handlebars',

    # Bluebottle apps
    'bluebottle.accounts',
    'bluebottle.common',
    'bluebottle.geo',
    )

MIDDLEWARE_CLASSES = [
    # Have a middleware to make sure old cookies still work after we switch to domain-wide cookies.
    'bluebottle.bluebottle_utils.middleware.SubDomainSessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # https://docs.djangoproject.com/en/1.4/ref/clickjacking/
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
]

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'bluebottle', 'test_files', 'templates'),
)

TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'apptemplates.Loader', # extend AND override templates
]

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    # Makes the 'request' variable (the current HttpRequest) available in templates.
    'django.core.context_processors.request',
    'django.core.context_processors.i18n'
)

AUTH_USER_MODEL = 'accounts.BlueBottleUser'


ROOT_URLCONF = 'bluebottle.urls'

SESSION_COOKIE_NAME = 'bb-session-id'

# Django-registration settings
ACCOUNT_ACTIVATION_DAYS = 4
HTML_ACTIVATION_EMAIL = True  # Note this setting is from our forked version.



SOUTH_TESTS_MIGRATE = False # Make south shut up during tests

SELENIUM_TESTS = True
SELENIUM_WEBDRIVER = 'phantomjs'  # Can be any of chrome, firefox, phantomjs

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


DEBUG = True
TEMPLATE_DEBUG = True

USE_EMBER_STYLE_ATTRS = True