from django.dispatch import Signal
from django.dispatch import receiver
from django_fsm.signals import pre_transition, post_transition

from bluebottle.payments.models import Payment, OrderPayment


payment_status_fetched = Signal(providing_args=["new_authorized_status"])
payment_status_changed = Signal(providing_args=["old_status", "new_status"])
order_payment_status_changed = Signal(providing_args=["old_status", "new_status"])

@receiver(post_transition, sender=Payment)
def _on_payment_status_changed(**kwargs):
    """
    TODO: Here we need to get the status from the payment and update the associated Order Payment.
          The mapping is currently one to one so we can handle a transition to the same status.
    """
    # Get the Order from the Signal 
    order_payment = kwargs['instance'].order_payment
     
    # Get the mapped status OrderPayment to Order
    new_order_payment_status = OrderPayment.status_mapping(kwargs['target'])
     
    order_payment.transition_to(new_order_payment_status)
