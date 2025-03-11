from djmoney.contrib.exchange.backends import OpenExchangeRatesBackend
from celery.schedules import crontab

from bluebottle.funding.models import Donor, Funding

from bluebottle.celery import app
from bluebottle.fsm.periodic_tasks import execute_tasks


@app.task
def funding_tasks():
    execute_tasks(Funding)


@app.task
def donor_tasks():
    execute_tasks(Donor)


@app.task
def update_rates():
    OpenExchangeRatesBackend().update_rates()


@app.on_after_finalize.connect
def schedule(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='*/15'),
        funding_tasks.s()
    )
    sender.add_periodic_task(
        crontab(minute='*/15'),
        donor_tasks.s()
    )

    sender.add_periodic_task(
        crontab(minute='*/15'),
        update_rates.s()
    )
