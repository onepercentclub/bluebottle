from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import Signal

from django_fsm.signals import pre_transition, post_transition

from bluebottle.utils.utils import StatusDefinition
from bluebottle.utils.model_dispatcher import get_model_class


order_status_changed = Signal(providing_args=["order"])
order_requested = Signal(providing_args=["order"])

@receiver(post_save, weak=False, dispatch_uid='donation_model')
def update_order_amount(sender, instance, **kwargs):
    if isinstance(instance, get_model_class('DONATIONS_DONATION_MODEL')):
        instance.order.update_total()


@receiver(post_delete, weak=False, dispatch_uid='donation_model')
def update_order_amount(sender, instance, **kwargs):
    if isinstance(instance, get_model_class('DONATIONS_DONATION_MODEL')):
        instance.order.update_total()


@receiver(post_transition)
def _order_payment_status_changed(sender, instance, **kwargs):
    from bluebottle.payments.models import OrderPayment
    if isinstance(instance, OrderPayment):
        """
        TODO: Here we need to get the status from the Order Payment and update the associated Order.
        """
        # Get the Order from the OrderPayment 
        order = instance.order
         
        # Get the mapped status OrderPayment to Order
        new_order_status = order.get_status_mapping(kwargs['target'])
         
        order.transition_to(new_order_status)

        # Trigger Order status changed signal
        order_status_changed.send(sender=order, order=order)


@receiver(order_requested)
def _order_requested(sender, order, **kwargs):
    from bluebottle.payments.services import PaymentService
    from bluebottle.payments.models import OrderPayment

    # Check the status at PSP if status is still locked
    if order.status == StatusDefinition.LOCKED:
        order_payment = OrderPayment.get_latest_by_order(order)
        service = PaymentService(order_payment)
        service.check_payment_status()
