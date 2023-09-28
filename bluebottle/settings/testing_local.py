from bluebottle.settings.testing import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'bluebottle.clients.postgresql_backend',
        'HOST': 'postgres',
        'PORT': '5432',
        'NAME': 'reef',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'DISABLE_SERVER_SIDE_CURSORS': True # this prevents issues with connection pooling
    },

}

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'elasticsearch:9200'
    },

}

SLOW_TEST_THRESHOLD_MS = 1000
ELASTICSEARCH_DSL_AUTOSYNC = False

CELERY_MAIL = False
