import logging

from celery.schedules import crontab
from bluebottle.celery import app

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

logger = logging.getLogger('bluebottle')


@app.task
def grant_provider_tasks():
    from bluebottle.grant_management.models import GrantProvider

    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in GrantProvider.get_periodic_tasks():
                task.execute()


@app.task
def check_grant_payment_readiness():
    from bluebottle.grant_management.models import GrantPayment

    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for payment in GrantPayment.objects.filter(status='pending'):
                payment.check_status()


app.add_periodic_task(
    crontab(minute='*/15'),
    grant_provider_tasks.s()
)

app.add_periodic_task(
    crontab(minute='*/20'),
    check_grant_payment_readiness.s()
)
