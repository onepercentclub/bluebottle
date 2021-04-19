from django.db import models
from django.utils.translation import gettext_lazy as _

from future.utils import python_2_unicode_compatible
from tenant_schemas.models import TenantMixin


@python_2_unicode_compatible
class Client(TenantMixin):
    name = models.CharField(max_length=100)
    client_name = models.CharField(max_length=100, unique=True)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'), auto_now=True)

    auto_create_schema = True

    def __str__(self):
        return self.name
