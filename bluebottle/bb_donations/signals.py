from bluebottle.bb_donations.donationmail import successful_donation_fundraiser_mail
from bluebottle.bb_orders.signals import order_status_changed
from bluebottle.utils.utils import StatusDefinition
from django.dispatch.dispatcher import receiver

@receiver(order_status_changed)
def _order_status_changed(sender, order, **kwargs):

    if order.status in [StatusDefinition.SUCCESS, StatusDefinition.FAILED]:
        for donation in order.donations.all():
            donation.project.update_amounts()

        if order.status == StatusDefinition.SUCCESS:
            for donation in order.donations.all():
                successful_donation_fundraiser_mail(donation)


