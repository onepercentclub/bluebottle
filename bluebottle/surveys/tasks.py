from __future__ import absolute_import

import logging

from django.core.management import call_command

from celery import shared_task

from bluebottle.clients.utils import LocalTenant

logger = logging.getLogger(__name__)


@shared_task
def sync_surveys():
    logger.info("Synchronzing all surveys")
    call_command('sync_surveys')
    logger.info("Finished synchronizing surveys")


@shared_task
def sync_survey(client, survey):
    logger.info("Synchronzing survey (webhook)")
    with LocalTenant(client, clear_tenant=True):
        survey.synchronize()
    logger.info("Finished synchronizing survey")
