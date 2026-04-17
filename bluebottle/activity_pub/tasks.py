from celery import shared_task
from bluebottle.clients.utils import LocalTenant


@shared_task(
    autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5},
    name="bluebottle.activity_pub.tasks.publish_to_recipient"
)
def publish_to_recipient(recipient, tenant):
    with LocalTenant(tenant, clear_tenant=True):
        recipient.publish()

@shared_task(
    autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5},
    name="bluebottle.activity_pub.adapters.publish_activities"
)
def publish_activity(recipient, activity, tenant):
    with LocalTenant(tenant, clear_tenant=True):
        event = Event.sync(activity)
        create = event.create_set.first()
        Recipient.objects.get_or_create(actor=recipient, activity=create)
