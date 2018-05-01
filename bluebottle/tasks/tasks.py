from __future__ import absolute_import

import logging

from celery import shared_task
from django.db import connection
from django.utils import timezone

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.tasks.models import Task
from bluebottle.tasks.taskmail import send_upcoming_task_reminder, TASK_REMINDER_INTERVAL

logger = logging.getLogger(__name__)


@shared_task
def send_task_reminder_mails():
    """
    Check if there are tasks due.
    """
    task_reminder_interval = TASK_REMINDER_INTERVAL  # days
    deadline = timezone.now() + timezone.timedelta(days=task_reminder_interval)

    logger.info("Sending task reminder mails.")
    for tenant in Client.objects.all():
        connection.set_tenant(tenant)
        with LocalTenant(tenant, clear_tenant=True):
            for task in Task.objects.filter(
                deadline__lte=deadline,
                deadline__gte=timezone.now()
            ):
                send_upcoming_task_reminder(task)
