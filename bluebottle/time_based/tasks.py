import logging

from celery.schedules import crontab

from bluebottle.celery import app

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
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
    RegisteredDateActivity
)

logger = logging.getLogger('bluebottle')

@app.on_after_configure.connect
def periodic_task(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='*/15'),
        date_activity_tasks.s()

    )

    sender.add_periodic_task(
        crontab(minute='*/15'),
        date_participant_tasks.s()
    )

    sender.add_periodic_task(
        crontab(minute='*/15'),
        registered_date_activity_tasks.s()
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
        schedule_activity_tasks.s()
    )

    sender.add_periodic_task(
        crontab(minute='*/15'),
        periodic_slot_tasks.s()
    )

    sender.add_periodic_task(
        crontab(minute='*/15'),
        schedule_slot_tasks.s()
    )

    sender.add_periodic_task(
        crontab(minute='*/15'),
        team_schedule_slot_tasks.s()
    )

    sender.add_periodic_task(
        crontab(minute='*/15'),
        team_schedule_slot_tasks.s()
    )

    sender.add_periodic_task(
        crontab(minute='*/15'),
        registered_date_activity_tasks.s()
    )

@app.task
def date_activity_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in DateActivity.get_periodic_tasks():
                task.execute()
            for task in DateActivitySlot.get_periodic_tasks():
                task.execute()


@app.task
def date_participant_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in DateParticipant.get_periodic_tasks():
                task.execute()


@app.task
def time_contribution_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in TimeContribution.get_periodic_tasks():
                task.execute()


@app.task
def deadline_activity_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in DeadlineActivity.get_periodic_tasks():
                task.execute()


@app.task
def periodic_activity_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in PeriodicActivity.get_periodic_tasks():
                task.execute()


@app.task
def schedule_activity_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in ScheduleActivity.get_periodic_tasks():
                task.execute()


@app.task
def periodic_slot_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in PeriodicSlot.get_periodic_tasks():
                task.execute()


@app.task
def schedule_slot_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in ScheduleSlot.get_periodic_tasks():
                task.execute()


@app.task
def team_schedule_slot_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in TeamScheduleSlot.get_periodic_tasks():
                task.execute()


@app.task
def registered_date_activity_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in RegisteredDateActivity.get_periodic_tasks():
                task.execute()
            for task in RegisteredDateActivity.get_periodic_tasks():
                task.execute()
