from celery import shared_task

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.sharing.consumers import consume_activities


@shared_task(bind=True)
def tenant_start_consumers(self, schema_name):
    tenant = Client.objects.get(schema_name=schema_name)
    print(f"Starting consumers for tenant {schema_name}")
    with LocalTenant(tenant):
        consume_activities(),
    print(f"Completed consumers for tenant {schema_name}")
