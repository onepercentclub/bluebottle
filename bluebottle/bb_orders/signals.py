from django.dispatch import Signal
from django.dispatch import receiver

from django_fsm.signals import pre_transition, post_transition

from bluebottle.utils.model_dispatcher import get_order_model
from bluebottle.payments.signals import order_payment_status_changed
from bluebottle.payments.models import OrderPayment

ORDER_MODEL = get_order_model()


@receiver(post_transition, sender=OrderPayment)
def _on_payment_status_changed(**kwargs):
    """
    TODO: Here we need to get the status from the Order Payment and update the associated Order.
    """
    # Get the Order from the Signal 
    order = kwargs['instance'].order
     
    # Get the mapped status OrderPayment to Order
    new_order_status = ORDER_MODEL.status_mapping.get(kwargs['target'], ORDER_MODEL.StatusDefinition.FAILED)
     
    order.transition_to(new_order_status)
    