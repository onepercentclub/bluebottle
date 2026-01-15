from bluebottle.settings.testing import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "bluebottle.clients.postgresql_backend",
        "HOST": os.environ.get("PGHOST", "localhost"),
        "PORT": os.environ.get("PGPORT", "5432"),
        "NAME": "bluebottle_test",
        "USER": "testuser",
        "PASSWORD": "password",
    },

}

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': os.environ.get("ESPORT", "localhost") + ':' + os.environ.get("ESPORT", "9200")
    },

}
