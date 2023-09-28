from bluebottle.settings.testing import *

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

SLOW_TEST_THRESHOLD_MS = 1000
