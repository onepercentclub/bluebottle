from __future__ import absolute_import

import logging

from django.core.management import call_command

from celery import shared_task

logger = logging.getLogger()


@shared_task
def set_status_realised():
    logger.info("Updating project statuses via Celery")
    call_command('cron_status_realised')
    logger.info("Finished updating project statuses via Celery")
