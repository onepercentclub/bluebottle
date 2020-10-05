from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
import json
import logging
import requests

from django.core.management import call_command

from urllib.parse import urljoin
from celery import shared_task
from sorl.thumbnail.shortcuts import get_thumbnail

from bluebottle.clients.utils import LocalTenant, tenant_url
from bluebottle.wallposts.models import MediaWallpost

logger = logging.getLogger(__name__)


@shared_task
def _send_celery_mail(msg, tenant=None, send=False):
    """
        Async function to send emails or do logging. For the logging we encode
        to utf_8 so we don't get Unicode errors.
    """
    with LocalTenant(tenant, clear_tenant=True):

        body = msg.body

        subject = msg.subject

        if send:
            try:
                logger.info(u"Trying to send mail to:\n\
                            recipients: {0}\n\
                            from: {1}\n\
                            subject: {2}\n\n".format(msg.to, msg.from_email,
                                                     subject))
                msg.send()

                logger.info(u"Succesfully sent mail:\n\
                            recipients: {0} \n\
                            from: {1}\n\
                            subject: {2} \n\
                            body:{3} \n\n"
                            .format(msg.to, msg.from_email,
                                    subject,
                                    body))
            except Exception as e:
                logger.error(u"Error sending mail: {0}".format(e))
                raise e
        else:
            logger.info((
                u"Sending mail off. Mail task received for msg:"
                u"recipients: {0}"
                u"from: {1} "
                u"subject: {2}"
                u"body:{3}"
            ).format(
                msg.to,
                msg.from_email,
                subject,
                body
            )
            )


@shared_task
def update_salesforce(tenant=None,
                      synchronize=False,
                      updated=False,
                      csv_export=False,
                      verbosity='2',
                      log_to_salesforce=False):
    logger.info("Updating Salesforce")

    try:
        call_command('sync_salesforce',
                     tenant=tenant,
                     synchronize=synchronize,
                     updated=updated,
                     verbosity=verbosity,
                     csv_export=csv_export,
                     log_to_salesforce=log_to_salesforce)
    except Exception as e:
        logger.error("Error running salesforce celery task: {0}".format(e))

    logger.info("Finished updating Salesforce")


@shared_task
def _post_to_facebook(instance, tenant=None):
    """ Post a Wallpost to users Facebook page using Celery """
    logger.info("FB post for:")
    logger.info("{0} with id {1} and tenant {2}".format(instance.__class__,
                                                        instance.id,
                                                        tenant.client_name))

    if not tenant:
        return

    with LocalTenant(tenant, clear_tenant=True):
        social = instance.author.social_auth.get(provider='facebook')
        authorization_header = 'Bearer {token}'.format(
            token=social.extra_data['access_token']
        )

        graph_url = 'https://graph.facebook.com/v2.4/me/feed'
        base_url = 'https://{domain}'.format(
            domain=tenant.domain_url)

        link = instance.content_object.get_absolute_url()

        image = None
        # This code is executed via Celery, we assume the MediaWallpostPhoto
        # is saved and available on the instance. If the user uploaded
        # photos with the MediaWallpost we take the first one and include it
        # in the Facebook post. Otherwise we fallback to the project image.
        if isinstance(instance, MediaWallpost) and instance.photos.count() > 0:
            image = urljoin(base_url,
                            get_thumbnail(instance.photos.all()[0].photo,
                                          "600x400").url
                            )
        else:
            if hasattr(instance.content_object, 'image') and instance.content_object.image:
                image = urljoin(
                    base_url,
                    get_thumbnail(instance.content_object.image, "600x400").url
                )

        description = getattr(
            instance.content_object, 'pitch', instance.content_object.description
        )

        data = {
            'link': link,
            'name': instance.content_object.title,
            'description': description,
            'message': instance.text,
            'picture': image,
            'caption': tenant_url()
        }

        # TODO: log failed requests
        requests.post(
            graph_url,
            data=json.dumps(data),
            headers={
                'Authorization': authorization_header,
                'Content-Type': 'application/json'}
        )
