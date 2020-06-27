from django.db import connection
from django.utils.decorators import ContextDecorator
from django.utils import translation

from tenant_extras.middleware import tenant_translation


class override(ContextDecorator):
    def __init__(self, language):
        self.language = language

    def __enter__(self):
        self.old_language = translation.get_language()
        translation.activate(self.language)
        translation._trans._active.value = tenant_translation(
            self.language or 'en', connection.tenant.client_name
        )

    def __exit__(self, exc_type, exc_value, traceback):
        translation.activate(self.old_language)
        translation._trans._active.value = tenant_translation(
            self.old_language or 'en', connection.tenant.client_name
        )
