import logging

from celery.schedules import crontab
from celery.task import periodic_task

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, TimeContribution
)

logger = logging.getLogger('bluebottle')


@periodic_task(
    run_every=(crontab(minute='*')),
    name="on_a_date_tasks",
    ignore_result=True
)
def on_a_date_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in DateActivity.get_periodic_tasks():
                task.execute()


@periodic_task(
    run_every=(crontab(minute='*')),
    name="with_a_deadline_tasks",
    ignore_result=True
)
def with_a_deadline_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in PeriodActivity.get_periodic_tasks():
                task.execute()


@periodic_task(
    run_every=(crontab(minute='*')),
    name="date_participant_tasks",
    ignore_result=True
)
def date_participant_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in DateParticipant.get_periodic_tasks():
                task.execute()


@periodic_task(
    run_every=(crontab(minute='*')),
    name="period_participant_tasks",
    ignore_result=True
)
def period_participant_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in PeriodParticipant.get_periodic_tasks():
                task.execute()


@periodic_task(
    run_every=(crontab(minute='*')),
    name="time_contribution_tasks",
    ignore_result=True
)
def time_contribution_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in TimeContribution.get_periodic_tasks():
                task.execute()
