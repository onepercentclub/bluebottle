import os

from bluebottle.settings.testing import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "bluebottle.clients.postgresql_backend",
        "HOST": os.environ.get("PGHOST", "localhost"),
        "PORT": os.environ.get("PGPORT", "5432"),
        "NAME": "bluebottle_test",
        "USER": "testuser",
        "PASSWORD": "password",
        "DISABLE_SERVER_SIDE_CURSORS": True,
        "MIGRATE": False,
    },

}

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'localhost:9200'
    },

}
