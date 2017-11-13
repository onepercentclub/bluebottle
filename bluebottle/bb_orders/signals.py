from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.dispatch.dispatcher import Signal

from django_fsm.signals import post_transition

from bluebottle.donations.models import Donation
from bluebottle.payments.models import OrderPayment
from bluebottle.payments.services import PaymentService
from bluebottle.utils.utils import StatusDefinition


order_requested = Signal(providing_args=["order"])


@receiver(post_save, weak=False, sender=Donation,
          dispatch_uid='donation_model')
def update_order_amount_post_save(sender, instance, **kwargs):
    instance.order.update_total()


@receiver(post_delete, weak=False, sender=Donation,
          dispatch_uid='donation_model')
def update_order_amount(sender, instance, **kwargs):
    # If we're deleting order and donations do nothing.
    # If we're just deleting a donation then we should update the order total.

    # Import it here to avoid circular imports
    from bluebottle.orders.models import Order
    try:
        instance.order.update_total()
    except Order.DoesNotExist:
        pass


@receiver(post_transition, sender=OrderPayment)
def _order_payment_status_changed(sender, instance, **kwargs):
    """
    TODO: Here we need to get the status from the Order Payment and update the
    associated Order.
    """
    # Get the Order from the OrderPayment
    order = instance.order

    order.process_order_payment_status_change(order_payment=instance, **kwargs)


@receiver(order_requested)
def _order_requested(sender, order, **kwargs):
    # Check the status at PSP if status is still locked
    if order.status == StatusDefinition.LOCKED:
        order_payment = OrderPayment.get_latest_by_order(order)
        service = PaymentService(order_payment)
        service.check_payment_status()
