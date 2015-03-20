from __future__ import absolute_import

import logging

from celery import shared_task

logger = logging.getLogger()


@shared_task
def _send_celery_mail(msg, send=False):

    if send:
        try:
            logger.info("Trying to send mail to:\n\
                        recipients: {0}\n\
                        subject: {1}\n\n".format(msg.to, msg.subject))
            msg.send()
            logger.info("Succesfully sent mail:\n\
                        recipients: {0} \n\
                        subject: {1} \n\
                        body:{2} \n\n"
                        .format(msg.to, msg.subject, msg.body))
        except Exception as e:
            logger.error("Error sending mail: {0}".format(e))
    else:
        logger.info("Sending mail off. Mail task received for msg:\n\
                    recipients: {0} \n\
                    subject: {1} \n\
                    body:{2} \n\n"
                    .format(msg.to, msg.subject, msg.body))
