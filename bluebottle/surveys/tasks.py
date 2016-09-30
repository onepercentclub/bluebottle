from __future__ import absolute_import

import logging

from django.core.management import call_command

from celery import shared_task

logger = logging.getLogger()


@shared_task
def sync_surveys():
    logger.info("Synchronzing all surveys")
    call_command('sync_surveys')
    logger.info("Finished synchronizing surveys")
