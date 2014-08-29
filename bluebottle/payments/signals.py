from django.dispatch import Signal
from django.dispatch import receiver
from django_fsm.signals import pre_transition, post_transition
from django.db.models.signals import pre_save, post_save, post_delete


payment_status_fetched = Signal(providing_args=['new_authorized_status'])

def set_previous_payment_status(sender, instance, **kwargs):
    # Store the previous status when the Payment is saved
    # so that it can be used on the next save to determine
    # if the status has changed.
    instance.previous_status = instance.status

def payment_status_changed(sender, instance, **kwargs):
    """
    TODO: Here we need to get the status from the payment and update the associated Order Payment.
          The mapping is currently one to one so we can handle a transition to the same status.
    """
    # Get the Order from the Signal 
    order_payment = instance.order_payment
     
    # Get the mapped status OrderPayment to Order
    new_order_payment_status = order_payment.get_status_mapping(instance.status)
     
    # Trigger status transition for OrderPayment
    order_payment.transition_to(new_order_payment_status)
