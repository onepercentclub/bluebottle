from __future__ import absolute_import

import logging

from celery import shared_task
from django.core.management import call_command
from django.db import connection

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.payments.services import PaymentService

logger = logging.getLogger(__name__)


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
    from bluebottle.projects.models import Project

    logger.info("Updating projects popularity using Celery")

    for tenant in Client.objects.all():
        connection.set_tenant(tenant)
        with LocalTenant(tenant, clear_tenant=True):
            Project.update_popularity()

    logger.info("Finished updating projects popularity using Celery")


@shared_task
def update_exchange_rates():
    """ Update the popularity score of all the projects

    Simply loops over all the tenants, and updates the scores
    """
    from bluebottle.projects.models import Project

    logger.info("Retrieving up to date exchange rates")
    # call_command('update_rates')

    logger.info("Updating amounts of all running projects")
    for tenant in Client.objects.all():
        connection.set_tenant(tenant)
        with LocalTenant(tenant, clear_tenant=True):
            for project in Project.objects.filter(status__slug='campaign'):
                project.update_amounts()


@shared_task
def update_project_status_stats():
    """ Calculates the no. of projects per status for a tenant
    """
    from bluebottle.projects.models import Project

    for tenant in Client.objects.all():
        connection.set_tenant(tenant)
        with LocalTenant(tenant, clear_tenant=True):
            Project.update_status_stats(tenant=tenant)


@shared_task
def refund_project(tenant, project):
    connection.set_tenant(tenant)
    with LocalTenant(tenant, clear_tenant=True):
        for donation in project.donations:
            service = PaymentService(donation.order.order_payment)
            service.refund_payment()
