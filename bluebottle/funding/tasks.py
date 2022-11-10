import logging

from celery.schedules import crontab
from celery.task import periodic_task
from djmoney.contrib.exchange.backends import OpenExchangeRatesBackend

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

logger = logging.getLogger('bluebottle')


@periodic_task(
    run_every=(crontab(hour='*/15')),
    name="funding_tasks",
    ignore_result=True
)
def funding_tasks():
    from bluebottle.funding.models import Funding
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in Funding.get_periodic_tasks():
                task.execute()


@periodic_task(
    run_every=(crontab(hour=2, minute=20)),
    name="donor_tasks",
    ignore_result=True
)
def donor_tasks():
    from bluebottle.funding.models import Donor
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in Donor.get_periodic_tasks():
                task.execute()


@periodic_task(
    run_every=(crontab(hour=3, minute=10)),
    name="update_rates",
    ignore_result=True
)
def update_rates():
    OpenExchangeRatesBackend().update_rates()
