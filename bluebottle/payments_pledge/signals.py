import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from bluebottle.donations.models import Donation
from bluebottle.payments.models import OrderPayment
from bluebottle.utils.utils import StatusDefinition

from .mails import mail_pledge_platform_admin

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=OrderPayment, dispatch_uid='payment_pledge_created')
def default_status_check(sender, instance, **kwargs):
    """
    - Get the status from the OrderPayment and send an email when ready.
    """
    if instance.payment_method != 'pledgeStandard':
        return

    if instance.previous_status in [StatusDefinition.CREATED] and instance.status in [StatusDefinition.PLEDGED]:
        try:
            donation = Donation.objects.filter(order__id=instance.order.id)[0]

            if donation:
                mail_pledge_platform_admin(donation)

        except IndexError:
            logger.critical('No pledge donation found matching Order ID: {0}'.format(instance.order.id))
