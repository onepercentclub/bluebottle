from bluebottle.settings.testing import *

# Database
DATABASES = {
    'default': {
        "ENGINE": "bluebottle.clients.postgresql_backend",
        "NAME": "bluebottle_test",
        "USER": "",
        "PASSWORD": "",
    },
}

SLOW_TEST_THRESHOLD_MS = 1000
