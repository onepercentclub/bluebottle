import logging

from celery import shared_task
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


@shared_task(name='bluebottle.activities.tasks.send_activity_message_notification_email')
def send_activity_message_notification_email(activity_message_id, tenant):
    from bluebottle.activities.models import ActivityMessage
    from bluebottle.clients.utils import LocalTenant
    from bluebottle.utils.email_backend import send_mail

    with LocalTenant(tenant, clear_tenant=True):
        try:
            instance = ActivityMessage.objects.select_related(
                'sender',
                'activity',
                'activity__owner',
            ).get(pk=activity_message_id)
        except ActivityMessage.DoesNotExist:
            logger.warning(
                'ActivityMessage id=%s not found for notification email',
                activity_message_id,
            )
            return

        owner = instance.activity.owner
        sender = instance.sender
        try:
            send_mail(
                template_name='mails/messages/activity_message_to_manager',
                subject=_('New message about your activity “{title}”').format(
                    title=instance.activity.title
                ),
                to=owner,
                reply_to=sender.email,
                recipient_name=owner.first_name or owner.full_name,
                sender_name=sender.full_name,
                title=instance.activity.title,
                message_text=instance.message,
                action_link=instance.activity.get_absolute_url(),
            )
        except Exception:
            logger.exception(
                'Failed to send activity message notification to activity owner'
            )
