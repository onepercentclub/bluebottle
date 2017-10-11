from django.db.models.signals import post_save
from django.dispatch import Signal
from django.dispatch import receiver

from django_fsm.signals import post_transition

from bluebottle.utils.utils import StatusDefinition
from .models import Payment, OrderPayment
from .mails import order_payment_refund_mail

payment_status_fetched = Signal(providing_args=['new_authorized_status'])


@receiver(post_save, weak=False, sender=OrderPayment,
          dispatch_uid='order_payment_model')
def order_payment_changed(sender, instance, **kwargs):
    # Send status change notification when record first created
    # This is to ensure any components listening for a status
    # on an OrderPayment will also receive the initial status.

    default_status = StatusDefinition.CREATED

    # Signal new status if current status is the default value
    if (instance.status == default_status):
        signal_kwargs = {
            'sender': sender,
            'instance': instance,
            'target': instance.status
        }
        post_transition.send(**signal_kwargs)


@receiver(post_save, weak=False, dispatch_uid='payments_previous_status')
def set_previous_status(sender, instance, **kwargs):
    if not (isinstance(instance, Payment) or isinstance(instance, OrderPayment)):
        return

    # Store the previous status when the Instance is saved
    # so that it can be used on the next save to determine
    # if the status has changed.
    instance.previous_status = instance.status


@receiver(post_save, weak=False, dispatch_uid='payment_model_change_status')
def payment_status_changed(sender, instance, **kwargs):
    """
    TODO: Here we need to get the status from the payment and update the
    associated Order Payment. The mapping is currently one to one so we can
    handle a transition to the same status.
    """
    if not isinstance(instance, Payment):
        return

    # Get the Order from the Signal
    order_payment = instance.order_payment

    # Set the fee on OrderPayment
    order_payment.transaction_fee = instance.get_fee()

    # Get the mapped status OrderPayment to Order
    new_order_payment_status = order_payment.get_status_mapping(instance.status)

    # Trigger status transition for OrderPayment
    order_payment.transition_to(new_order_payment_status)


@receiver(post_transition, weak=False, dispatch_uid='order_payment_refund')
def _order_payment_refund(sender, instance, **kwargs):
    """
    Handle Order Payment refund status.
    """
    if not isinstance(instance, OrderPayment):
        return

    if dict.get(kwargs, 'source', None) is not StatusDefinition.REFUNDED and \
       kwargs['target'] is StatusDefinition.REFUNDED:

        order_payment_refund_mail(instance)


@receiver(post_save, weak=False, dispatch_uid='default_status')
def default_status_check(sender, instance, **kwargs):
    if not isinstance(instance, OrderPayment):
        return

    # Send status change notification when record first created
    # This is to ensure any components listening for a status
    # on the Sender will also receive the initial status.

    # Get the default status for the status field on Sender
    default_status = StatusDefinition.CREATED

    from bluebottle.payments_logger.adapters import PaymentLogAdapter

    # adding a Log when the status changes
    payment_logger = PaymentLogAdapter()

    try:
        # if there is no Payment associated to the order_payment do not log
        # The log will be created in the adapter
        payment = Payment.objects.get(order_payment=instance)
        payment_logger.log(payment, 'info',
                           'a new payment status {0}'.format(instance.status))

    except Payment.DoesNotExist:
        pass
    except Payment.MultipleObjectsReturned:
        payment = Payment.objects.order('-created').filter(
            order_payment=instance).all()[0]
        payment_logger.log(payment, 'info',
                           'a new payment status {0}'.format(instance.status))
    finally:
        # Signal new status if current status is the default value
        if (instance.status == default_status):
            signal_kwargs = {
                'sender': sender,
                'instance': instance,
                'target': instance.status
            }
            post_transition.send(**signal_kwargs)
