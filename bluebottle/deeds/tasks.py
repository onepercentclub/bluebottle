from celery.schedules import crontab
from bluebottle.celery import app

from bluebottle.deeds.models import Deed
from bluebottle.fsm.periodic_tasks import execute_tasks


@app.on_after_finalize.connect
def schedule_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='*/15'),
        execute_tasks.s(Deed)
    )
