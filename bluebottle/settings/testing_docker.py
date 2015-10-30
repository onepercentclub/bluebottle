from .testing import *

DEFAULT_DB_ALIAS = 'default'
DATABASES = {
    'default': {
        'ENGINE': 'tenant_schemas.postgresql_backend',
        'HOST': 'postgresql',
        'PORT': '5432',
        'NAME': 'bluebottle_test',
        'USER': 'reef',
        'PASSWORD': 'reef'
    }
}
