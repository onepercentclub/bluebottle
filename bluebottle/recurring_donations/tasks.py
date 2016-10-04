from __future__ import absolute_import

import logging

from django.db import connection

from celery import shared_task

from bluebottle.clients.utils import LocalTenant
from bluebottle.recurring_donations.utils import process_monthly_batch

logger = logging.getLogger()


@shared_task
def process_batch_task(client, batch):
    logger.info("Process monthly batch")
    connection.set_tenant(client)
    with LocalTenant(client, clear_tenant=True):
        process_monthly_batch(batch)
    logger.info("Finished processing monthly batch")
