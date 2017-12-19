from __future__ import absolute_import
import logging
from celery import shared_task

from bluebottle.clients.utils import LocalTenant
from bluebottle.clients import properties

logger = logging.getLogger(__name__)


@shared_task
def send_mail(recipient, sender, subject, message, tenant=None, send=False):
    """
    Async function to send emails.
    """
    with LocalTenant(tenant, clear_tenant=True):
        if tenant:
            properties.set_tenant(tenant)

        if isinstance(message, unicode):
            message = message.encode('utf_8')

        if isinstance(subject, unicode):
            subject = subject.encode('utf_8')

        if send:
            # Actually send the mail
            pass
        else:
            # Don't send, just log
            pass
