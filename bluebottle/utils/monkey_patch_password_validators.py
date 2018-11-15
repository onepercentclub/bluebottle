import django.contrib.auth.password_validation
from django.utils import lru_cache

from bluebottle.clients import properties


def tenant_aware_get_default_password_validators():
    return django.contrib.auth.password_validation.get_password_validators(
        properties.AUTH_PASSWORD_VALIDATORS
    )


django.contrib.auth.password_validation.get_default_password_validators = tenant_aware_get_default_password_validators
