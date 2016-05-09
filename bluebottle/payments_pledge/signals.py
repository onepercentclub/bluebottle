import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from bluebottle.payments.models import OrderPayment
from bluebottle.utils.model_dispatcher import get_donation_model
from bluebottle.utils.utils import StatusDefinition

from .mails import mail_pledge_platform_admin

logger = logging.getLogger(__name__)


@receiver(post_save, weak=False, dispatch_uid='payment_pledge_created')
def default_status_check(sender, instance, **kwargs):
    if not isinstance(instance, OrderPayment):
        return

    if instance.payment_method != 'pledgeStandard':
        return

    if instance.status in [StatusDefinition.PLEDGED]:

        DONATION_MODEL = get_donation_model()
        try:
            donation = DONATION_MODEL.objects.filter(order__id=instance.order.id)[0]

            # NOTE: Only handling a single donation per order
            if donation:
                mail_pledge_platform_admin(donation)

        except IndexError as e:
            logger.critical('No pledge donation found matching Order ID: {0}'.format(instance.order.id))
            