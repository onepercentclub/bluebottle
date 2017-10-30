from .base import *
from .testing import *

DATABASES = {
    'default': {
        'ENGINE': 'tenant_schemas.postgresql_backend',
        'HOST': 'db',
        'PORT': '',
        'NAME': 'bluebottle_test',
        'USER': 'postgres',
        'PASSWORD': 'postgres'
    }
}
