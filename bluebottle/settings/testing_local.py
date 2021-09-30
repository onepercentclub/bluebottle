from bluebottle.settings.testing import *

# Database
DATABASES = {
    'default': {
        "ENGINE": "bluebottle.clients.postgresql_backend",
        "NAME": "test_reef",
        "USER": "",
        "PASSWORD": "",
    },
}

SLOW_TEST_THRESHOLD_MS = 1000
