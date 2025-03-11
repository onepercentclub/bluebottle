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


@app.task
def date_activity_tasks(sender, **kwargs):
    execute_tasks(DateActivity)


@app.task
def date_activity_slot_tasks(sender, **kwargs):
    execute_tasks(DateActivitySlot)


@app.task
def date_participant_tasks(sender, **kwargs):
    execute_tasks(DateParticipant)


@app.task
def time_contribution_tasks(sender, **kwargs):
    execute_tasks(TimeContribution)


@app.task
def deadline_activity_tasks(sender, **kwargs):
    execute_tasks(DeadlineActivity)


@app.task
def periodic_activity_tasks(sender, **kwargs):
    execute_tasks(PeriodicActivity)


@app.task
def periodic_slot_tasks(sender, **kwargs):
    execute_tasks(PeriodicSlot)


@app.task
def schedule_activity_tasks(sender, **kwargs):
    execute_tasks(ScheduleActivity)


@app.task
def schedule_slot_tasks(sender, **kwargs):
    execute_tasks(ScheduleSlot)


@app.task
def team_schedule_slot_tasks(sender, **kwargs):
    execute_tasks(TeamScheduleSlot)


@app.on_after_finalize.connect
def schedule(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='*/15'),
        date_activity_tasks.s()
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        date_activity_slot_tasks.s()
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        date_participant_tasks.s()
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        time_contribution_tasks.s()
    )

    sender.add_periodic_task(
        crontab(minute='*/15'),
        deadline_activity_tasks.s()
    )

    sender.add_periodic_task(
        crontab(minute='*/15'),
        periodic_activity_tasks.s()
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        periodic_slot_tasks.s()
    )

    sender.add_periodic_task(
        crontab(minute='*/15'),
        schedule_activity_tasks.s()
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        schedule_slot_tasks.s()
    )

    sender.add_periodic_task(
        crontab(minute='*/15'),
        team_schedule_slot_tasks.s()
    )
