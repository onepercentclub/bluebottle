import logging

from celery.schedules import crontab
from celery.task import periodic_task

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, TimeContribution, DateActivitySlot,
    PeriodActivitySlot, TeamSlot
)

logger = logging.getLogger('bluebottle')


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="date_activity_tasks",
    ignore_result=True
)
def date_activity_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in DateActivity.get_periodic_tasks():
                task.execute()
            for task in DateActivitySlot.get_periodic_tasks():
                task.execute()


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="with_a_deadline_tasks",
    ignore_result=True
)
def with_a_deadline_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in PeriodActivity.get_periodic_tasks():
                task.execute()


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="team_slot_tasks",
    ignore_result=True
)
def team_slot_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in TeamSlot.get_periodic_tasks():
                task.execute()


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="date_participant_tasks",
    ignore_result=True
)
def date_participant_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in DateParticipant.get_periodic_tasks():
                task.execute()


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="period_participant_tasks",
    ignore_result=True
)
def period_participant_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in PeriodParticipant.get_periodic_tasks():
                task.execute()


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="time_contribution_tasks",
    ignore_result=True
)
def time_contribution_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in TimeContribution.get_periodic_tasks():
                task.execute()


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="period_activity_slot_tasks",
    ignore_result=True
)
def period_activity_slot_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in PeriodActivitySlot.get_periodic_tasks():
                task.execute()
