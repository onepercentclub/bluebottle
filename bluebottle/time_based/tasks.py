import logging

from celery.schedules import crontab
from celery.task import periodic_task

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, Duration
)

logger = logging.getLogger('bluebottle')


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="on_a_date_tasks",
    ignore_result=True
)
def on_a_date_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in DateActivity.get_periodic_tasks():
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
    name="on_a_date_application_tasks",
    ignore_result=True
)
def on_a_date_application_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in DateParticipant.get_periodic_tasks():
                task.execute()


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="period_application_tasks",
    ignore_result=True
)
def period_application_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in PeriodParticipant.get_periodic_tasks():
                task.execute()


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="duration_tasks",
    ignore_result=True
)
def duration_tasks():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in Duration.get_periodic_tasks():
                task.execute()
