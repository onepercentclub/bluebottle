from bluebottle.settings.testing import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "bluebottle.clients.postgresql_backend",
        "HOST": "postgres",
        "PORT": "5432",
        "NAME": "bluebottle_test",
        "USER": "postgres",
        "PASSWORD": "password",
        "DISABLE_SERVER_SIDE_CURSORS": True,
        "MIGRATE": False,
    },

}

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'elasticsearch:9200'
    },

}
