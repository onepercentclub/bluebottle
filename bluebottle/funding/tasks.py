import logging

from celery.schedules import crontab
from celery.task import periodic_task

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

logger = logging.getLogger('bluebottle')


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="funding_tasks",
    ignore_result=True
)
def funding_tasks():
    from bluebottle.funding.models import Funding
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in Funding.get_periodic_tasks():
                task.execute()
