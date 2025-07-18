import logging

from celery.schedules import crontab
from celery.task import periodic_task

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

logger = logging.getLogger('bluebottle')


@periodic_task(
    run_every=(crontab(hour=8, minute=0, day_of_week=1)),
    name="grant_provider_tasks",
    ignore_result=True,
)
def grant_provider_tasks():
    from bluebottle.grant_management.models import GrantProvider

    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in GrantProvider.get_periodic_tasks():
                task.execute()
