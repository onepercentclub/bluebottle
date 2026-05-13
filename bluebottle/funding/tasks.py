import logging

from celery.schedules import crontab
from bluebottle.celery import app
from djmoney.contrib.exchange.backends import OpenExchangeRatesBackend

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

logger = logging.getLogger('bluebottle')

from celery.utils.log import get_task_logger

@app.task
def funding_tasks():
    from bluebottle.funding.models import Funding
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in Funding.get_periodic_tasks():
                task.execute()


@app.task
def donor_tasks():
    from bluebottle.funding.models import Donor
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in Donor.get_periodic_tasks():
                task.execute()


@app.task
def update_rates():
    OpenExchangeRatesBackend().update_rates()


app.add_periodic_task(
    crontab(minute='*/1'),
    funding_tasks.s()
)

app.add_periodic_task(
    crontab(hour=2, minute=20),
    donor_tasks.s()
)

app.add_periodic_task(
    crontab(hour=2, minute=20),
    update_rates.s()
)
