import logging

from celery import shared_task
from bluebottle.clients.utils import LocalTenant

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5},
    name="bluebottle.activity_pub.adapters.publish_to_recipient"
)
def publish_to_recipient(activity, recipient, tenant):
    """Celery task to publish an activity to a specific recipient."""
    from bluebottle.activity_pub.adapters import adapter
    from bluebottle.activity_pub.serializers.json_ld import ActivitySerializer

    with LocalTenant(tenant, clear_tenant=True):
        actor = recipient.actor
        inbox = getattr(actor, "inbox", None)
        if recipient.send:
            pass
        actor = recipient.actor
        if inbox is None or inbox.is_local:
            logger.warning(f"Actor {actor} has no inbox, skipping publish")
            pass
        try:
            data = ActivitySerializer().to_representation(activity)
            auth = adapter.get_auth(activity.actor)
            adapter.post(inbox.iri, data=data, auth=auth)
            recipient.send = True
            recipient.save()
        except Exception as e:
            logger.error(f"Error in publish_to_recipient: {type(e).__name__}: {str(e)}", exc_info=True)
            raise


# Note: publish_activity is a signal handler defined in adapters.py, not a Celery task
# It doesn't need to be imported here for Celery autodiscovery
