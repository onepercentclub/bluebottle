from django.db import connection
from django.db.models.signals import post_save
from django.dispatch import receiver

from bluebottle.activities.models import ActivityMessage
from bluebottle.activities.tasks import send_activity_message_notification_email


@receiver(post_save, sender=ActivityMessage)
def activity_message_notify_owner_on_create(sender, instance, created, **kwargs):
    if not created:
        return
    send_activity_message_notification_email.delay(instance.pk, connection.tenant)
