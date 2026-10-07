import logging

from celery.schedules import crontab
from bluebottle.celery import app

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.voting.models import Poll

logger = logging.getLogger('bluebottle')


@app.task
def poll_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in Poll.get_periodic_tasks():
                task.execute()


app.add_periodic_task(
    crontab(minute='*/15'),
    poll_tasks.s()
)
