from datetime import timedelta
from celery.schedules import crontab
from celery.task import periodic_task
from django.utils.timezone import now

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
import logging

from bluebottle.assignments.models import Assignment
from bluebottle.assignments.messages import (
    AssignmentReminderDeadline, AssignmentReminderOnDate
)

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
                registration_deadline__lte=now(),
                status__in=['full', 'open']
            ).all()

            for assignment in assignments:
                assignment.save()


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="check_assignment_start_date",
    ignore_result=True
)
def check_assignment_start_date():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            # Close assignments passed registration_deadline
            assignments = Assignment.objects.filter(
                date__lte=now(),
                status__in=['full', 'open']
            ).all()

            for assignment in assignments:
                assignment.save()


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
                date__lt=now(),
                status__in=['full', 'open', 'running']
            ).all()

            for assignment in assignments:
                assignment.save()


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="check_assignment_reminder",
    ignore_result=True
)
def check_assignment_reminder():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            # Close assignment that are over
            assignments = Assignment.objects.filter(
                date__lte=now() + timedelta(days=5),
                status__in=['open', 'full'],
            ).all()

            for assignment in assignments:
                if assignment.end_date_type == 'deadline':
                    AssignmentReminderDeadline(assignment).compose_and_send()
                else:
                    AssignmentReminderOnDate(assignment).compose_and_send()
