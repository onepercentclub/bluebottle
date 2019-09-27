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
    name="check_assignment_registration_deadline",
    ignore_result=True
)
def check_assignment_registration_deadline():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            # Close assignments passed registration_deadline
            assignments = Assignment.objects.filter(
                end_date__lte=now(),
                status__in=['full', 'open']
            ).all()

            for assignment in assignments:
                assignment.registration_deadline_passed()


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="check_assignment_end_date",
    ignore_result=True
)
def check_assignment_end_date():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            # Close assignments passed end_date
            assignments = Assignment.objects.filter(
                end_date__lte=now(),
                status__in=['full', 'open', 'running']
            ).all()

            for assignment in assignments:
                assignment.end_date_passed()
