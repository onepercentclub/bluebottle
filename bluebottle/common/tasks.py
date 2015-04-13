from __future__ import absolute_import

import logging

from celery import shared_task

logger = logging.getLogger()


@shared_task
def _send_celery_mail(msg, send=False):
    """
        Async function to send emails or do logging. For the logging we encode
        to utf_8 so we don't get Unicode errors.
    """
    if send:
        try:
            logger.info("Trying to send mail to:\n\
                        recipients: {0}\n\
                        from: {1}\n\
                        subject: {2}\n\n".format(msg.to, msg.from_email,
                                                 msg.subject.encode('utf_8')))
            msg.send()
            logger.info("Succesfully sent mail:\n\
                        recipients: {0} \n\
                        from: {1}\n\
                        subject: {2} \n\
                        body:{3} \n\n"
                        .format(msg.to, msg.from_email,
                                msg.subject.encode('utf_8'),
                                msg.body.encode('utf_8')))
        except Exception as e:
            logger.error("Error sending mail: {0}".format(e))
    else:
        logger.info("Sending mail off. Mail task received for msg:\n\
                    recipients: {0} \n\
                    from: {1} \n\
                    subject: {2} \n\
                    body:{3} \n\n"
                    .format(msg.to, msg.from_email,
                            msg.subject.encode('utf_8'),
                            msg.body.encode('utf_8')))
