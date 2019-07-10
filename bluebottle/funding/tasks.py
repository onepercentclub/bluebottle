from celery.schedules import crontab
from celery.task import periodic_task
from django.utils.timezone import now

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
import logging

logger = logging.getLogger('bluebottle')


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="check_funding_end",
    ignore_result=True
)
def check_funding_end():
    from bluebottle.funding.models import Funding
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):

            # Close funding activities that are over deadline
            activities = Funding.objects.filter(
                deadline__lte=now(),
                status__in=['running']
            ).all()

            for funding in activities:
                if funding.amount_raised >= funding.target:
                    funding.transitions.succeed()
                else:
                    funding.transitions.partial()
                funding.save()
