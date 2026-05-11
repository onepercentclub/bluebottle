import logging

from celery.schedules import crontab
from bluebottle.celery import app

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.collect.models import CollectActivity

logger = logging.getLogger('bluebottle')


@app.on_after_configure.connect
def periodic_task(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='*/15'),
        collect_tasks.s()
    )


@app.task
def collect_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in CollectActivity.get_periodic_tasks():
                task.execute()
