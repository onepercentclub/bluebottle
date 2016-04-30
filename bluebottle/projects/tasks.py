from __future__ import absolute_import

import logging

from django.core.management import call_command
from django.db import connection

from celery import shared_task

from bluebottle.clients.utils import LocalTenant
from bluebottle.clients.models import Client
from bluebottle.projects.models import Project

logger = logging.getLogger()


@shared_task
def set_status_realised():
    logger.info("Updating project statuses via Celery")
    call_command('cron_status_realised')
    logger.info("Finished updating project statuses via Celery")


@shared_task
def update_popularity():
    """ Update the popularity score of all the projects

    Simply loops over all the tenants, and updates the scores
    """
    logger.info("Updating projects popularity using Celery")

    for tenant in Client.objects.all():
        connection.set_tenant(tenant)
        with LocalTenant(tenant, clear_tenant=True):
            Project.update_popularity()

    logger.info("Finished updating projects popularity using Celery")
