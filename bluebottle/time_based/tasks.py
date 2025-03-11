from celery.schedules import crontab

from bluebottle.celery import app
from bluebottle.fsm.periodic_tasks import execute_tasks

from bluebottle.time_based.models import (
    DateActivity,
    DeadlineActivity,
    DateParticipant,
    PeriodicActivity,
    PeriodicSlot,
    TimeContribution,
    DateActivitySlot,
    ScheduleSlot,
    TeamScheduleSlot,
    ScheduleActivity,
)


@app.on_after_finalize.connect
def schedule_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='*/15'),
        execute_tasks.s(DateActivity)
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        execute_tasks.s(DateActivitySlot)
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        execute_tasks.s(DateParticipant)
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        execute_tasks.s(TimeContribution)
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        execute_tasks.s(DeadlineActivity)
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        execute_tasks.s(PeriodicActivity)
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        execute_tasks.s(ScheduleActivity)
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        execute_tasks.s(PeriodicSlot)
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        execute_tasks.s(ScheduleSlot)
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        execute_tasks.s(TeamScheduleSlot)
    )
