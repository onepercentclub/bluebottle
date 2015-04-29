from __future__ import absolute_import

import logging

from django.core.management import call_command

from celery import shared_task

logger = logging.getLogger()


@shared_task
def _send_celery_mail(msg, send=False):
    """
        Async function to send emails or do logging. For the logging we encode
        to utf_8 so we don't get Unicode errors.
    """
    body = msg.body
    if isinstance(body, unicode):
        body = msg.body.encode('utf_8')

    subject = msg.subject
    if isinstance(subject, unicode):
        subject = msg.subject.encode('utf_8')

    if send:
        try:
            logger.info("Trying to send mail to:\n\
                        recipients: {0}\n\
                        from: {1}\n\
                        subject: {2}\n\n".format(msg.to, msg.from_email,
                                                 subject))
            msg.send()

            logger.info("Succesfully sent mail:\n\
                        recipients: {0} \n\
                        from: {1}\n\
                        subject: {2} \n\
                        body:{3} \n\n"
                        .format(msg.to, msg.from_email,
                                subject,
                                body))
        except Exception as e:
            logger.error("Error sending mail: {0}".format(e))
            raise e
    else:
        logger.info("Sending mail off. Mail task received for msg:\n\
                    recipients: {0} \n\
                    from: {1} \n\
                    subject: {2} \n\
                    body:{3} \n\n"
                    .format(msg.to, msg.from_email,
                            subject,
                            body))


@shared_task
def update_salesforce(tenant=None,
                      synchronize=False,
                      updated=60,
                      csv_export=False,
                      verbosity='3'):
    logger.info("Updating Salesforce")

    try:
        call_command('sync_salesforce',
                     tenant=tenant,
                     synchronize=synchronize,
                     updated=updated,
                     verbosity=verbosity,
                     csv_export=csv_export)
    except Exception as e:
        logger.error("Error running salesforce celery task: {0}".format(e))

    logger.info("Finished updating Salesforce")
