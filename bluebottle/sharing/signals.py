from django.db import connection
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from bluebottle.sharing.models import PlatformConnection
from bluebottle.sharing.tasks import tenant_start_consumers


@receiver(post_save, sender=PlatformConnection)
@receiver(post_delete, sender=PlatformConnection)
def trigger_tenant_start_consumers(sender, instance, **kwargs):
    schema_name = connection.tenant.schema_name
    print(f"Task triggered for {schema_name}")
    tenant_start_consumers.apply_async(args=[schema_name])
