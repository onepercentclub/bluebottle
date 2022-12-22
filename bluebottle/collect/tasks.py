import logging

from celery.schedules import crontab
from celery.task import periodic_task

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.collect.models import CollectActivity

logger = logging.getLogger('bluebottle')


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="collect_tasks",
    ignore_result=True
)
def collect_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in CollectActivity.get_periodic_tasks():
                task.execute()
