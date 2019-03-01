from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.dispatch.dispatcher import Signal
from django.utils import timezone
from django_fsm.signals import post_transition

from bluebottle.clients import properties
from bluebottle.donations.donationmail import (
    new_oneoff_donation, successful_donation_fundraiser_mail
)
from bluebottle.donations.models import Donation
from bluebottle.orders.models import Order
from bluebottle.orders.tasks import timeout_new_order, timeout_locked_order
from bluebottle.payments.models import OrderPayment
from bluebottle.payments.services import PaymentService
from bluebottle.utils.utils import StatusDefinition
from bluebottle.wallposts.models import SystemWallpost, TextWallpost

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


@receiver(post_save, sender=Order)
def _order_status_post_save(sender, instance, **kwargs):
    """
    - Update amount on project when order is in an ending status.
    """

    if instance.status in [
        StatusDefinition.SUCCESS, StatusDefinition.PENDING,
        StatusDefinition.REFUNDED, StatusDefinition.REFUND_REQUESTED,
        StatusDefinition.PLEDGED, StatusDefinition.FAILED,
        StatusDefinition.CANCELLED
    ]:

        # Process each donation in the order
        for donation in instance.donations.all():
            # Update amounts for the associated project
            donation.project.update_amounts()


@receiver(post_transition, sender=Order)
def _order_status_post_transition(sender, instance, **kwargs):
    """
    - Get the status from the Order and Send an Email.
    """

    if instance.status in [StatusDefinition.SUCCESS, StatusDefinition.PENDING,
                           StatusDefinition.PLEDGED]:
        # Is order transitioning into the success or pending state - this should
        # only happen once.

        first_time_success = (
            kwargs['source'] not in [StatusDefinition.PLEDGED,
                                     StatusDefinition.SUCCESS,
                                     StatusDefinition.PENDING] and
            kwargs['target'] in [StatusDefinition.PLEDGED,
                                 StatusDefinition.SUCCESS,
                                 StatusDefinition.PENDING]
        )

        # Process each donation in the order
        for donation in instance.donations.all():
            # Send mail / create wallposts if status transitions in to
            # success/pending for the first time and only if it's a
            # one-off donation.
            if first_time_success and instance.order_type == "one-off":
                if not donation.anonymous:
                    author = donation.order.user
                else:
                    author = None

                successful_donation_fundraiser_mail(donation)
                new_oneoff_donation(donation)

                if donation.fundraiser:
                    # Create Wallpost on fundraiser wall (if FR present)
                    SystemWallpost.objects.create(
                        content_type=ContentType.objects.get_for_model(
                            donation.fundraiser
                        ),
                        object_id=donation.fundraiser.pk,
                        related_type=ContentType.objects.get_for_model(
                            donation
                        ),
                        related_id=donation.pk,
                        donation=donation,
                        author=author,
                        ip_address='127.0.0.1'
                    )
                elif TextWallpost.objects.filter(donation=donation).count() == 0:
                    # Create Wallpost on project wall if there isn't a wallpost for this donation yet
                    SystemWallpost.objects.get_or_create(
                        content_type=ContentType.objects.get_for_model(
                            donation.project
                        ),
                        object_id=donation.project.pk,
                        related_type=ContentType.objects.get_for_model(
                            donation
                        ),
                        related_id=donation.pk,
                        donation=donation,
                        author=author,
                        ip_address='127.0.0.1'
                    )


@receiver(post_transition, sender=Order)
def cancel_order(sender, instance, target, **kwargs):
    """
    - Get the status from the Order and Send an Email.
    """
    if (
        target == StatusDefinition.REFUNDED and
        any(donation.project.status.slug == 'refunded' for donation in instance.donations.all())
    ):
        instance.transition_to(StatusDefinition.CANCELLED)


@receiver(post_save, sender=Order)
def _timeout_new_order(sender, instance, created=None, **kwargs):
    """
    Fail new order after 10 minutes
    """
    if created and getattr(properties, 'CELERY_RESULT_BACKEND', None):
        timeout_new_order.apply_async(
            [instance, connection.tenant],
            eta=timezone.now() + timedelta(minutes=10)
        )


@receiver(post_save, sender=OrderPayment)
def _timeout_locked_order(sender, instance, created=None, **kwargs):
    """
    Fail locked order after 3 hours
    """
    if created and getattr(properties, 'CELERY_RESULT_BACKEND', None):
        timeout_locked_order.apply_async(
            [instance.order, connection.tenant],
            eta=timezone.now() + timedelta(hours=3)
        )
