from celery.schedules import crontab
from celery.task import periodic_task
from django.utils.timezone import now

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
import logging

from bluebottle.assignments.models import Assignment

logger = logging.getLogger('bluebottle')


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="check_assignment_end",
    ignore_result=True
)
def check_assignment_end():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            # Close assignments passed deadline
            assignments = Assignment.objects.filter(
                end_date__lte=now(),
                status__in=['running']
            ).all()

            for assignment in assignments:
                assignment.deadline_passed()
