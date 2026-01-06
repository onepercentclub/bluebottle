import logging

from celery import shared_task

from bluebottle.clients.utils import LocalTenant

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5},
    name="bluebottle.activity_pub.tasks.update_linked_activity"
)
def update_linked_activity(event_id, tenant):
    """Update linked activity fields when Event is saved"""
    from bluebottle.activity_pub.models import Event

    with LocalTenant(tenant, clear_tenant=True):

        try:
            event = Event.objects.get(pk=event_id)
            linked_activity = event.linked_activity

            if linked_activity:
                from bluebottle.activity_pub.adapters import adapter
                adapter.link(event)
                logger.info(f"Updated linked activity {linked_activity.pk} for event {event.pk}")
        except Event.DoesNotExist:
            logger.warning(f"Event {event_id} not found, skipping linked activity update")
        except Exception as e:
            logger.error(f"Error updating linked activity for event {event_id}: {type(e).__name__}: {str(e)}",
                         exc_info=True)
            raise
