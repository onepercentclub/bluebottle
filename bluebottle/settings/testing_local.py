from bluebottle.settings.testing import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "bluebottle.clients.postgresql_backend",
        "HOST": "postgres",
        "PORT": "5432",
        "NAME": "reef",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "DISABLE_SERVER_SIDE_CURSORS": True,  # this prevents issues with connection pooling
        "MIGRATE": False,
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

DEBUG = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'INFO',
        },
        'bluebottle': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'INFO',
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console']
    }
}
