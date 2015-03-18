from __future__ import absolute_import

import logging

from celery import shared_task


logger = logging.getLogger()


@shared_task
def _send_celery_mail(msg):
    try:
        msg.send()
    except Exception as e:
        logger.error("Error sending mail: {0}".format(e))
