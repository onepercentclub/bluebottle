from celery.schedules import crontab
from bluebottle.celery import app

from bluebottle.collect.models import CollectActivity
from bluebottle.fsm.periodic_tasks import execute_tasks


@app.task
def collect_tasks():
    execute_tasks(CollectActivity)


@app.on_after_finalize.connect
def schedule(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='*/15'),
        collect_tasks.s()
    )
