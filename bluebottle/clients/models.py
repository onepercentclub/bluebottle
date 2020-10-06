from django.db import models
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField
from future.utils import python_2_unicode_compatible
from tenant_schemas.models import TenantMixin


@python_2_unicode_compatible
class Client(TenantMixin):
    name = models.CharField(max_length=100)
    client_name = models.CharField(max_length=100, unique=True)
    created = CreationDateTimeField()
    updated = ModificationDateTimeField()

    auto_create_schema = True

    def __str__(self):
        return self.name
