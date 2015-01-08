from django.db import models
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField
from tenant_schemas.models import TenantMixin

class Client(TenantMixin):
    name = models.CharField(max_length=100)
    client_name = models.CharField(max_length=100, unique=True)
    created = CreationDateTimeField()
    updated = ModificationDateTimeField()

    auto_create_schema = True

