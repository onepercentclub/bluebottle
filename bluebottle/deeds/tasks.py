from celery.schedules import crontab
from bluebottle.celery import app

from bluebottle.deeds.models import Deed
from bluebottle.fsm.periodic_tasks import execute_tasks


@app.task
def deed_tasks():
    execute_tasks(Deed)


@app.on_after_finalize.connect
def schedule(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='*/15'),
        deed_tasks.s()
    )
