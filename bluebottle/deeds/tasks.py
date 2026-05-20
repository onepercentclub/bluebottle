import logging

from celery.schedules import crontab
from bluebottle.celery import app

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.deeds.models import Deed

logger = logging.getLogger('bluebottle')


@app.task
def deed_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in Deed.get_periodic_tasks():
                task.execute()


app.add_periodic_task(
    crontab(minute='*/15'),
    deed_tasks.s()
)
