from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save

from django_fsm.signals import post_transition

from bluebottle.donations.donationmail import (
    new_oneoff_donation, successful_donation_fundraiser_mail)
from bluebottle.orders.models import Order
from bluebottle.utils.utils import StatusDefinition
from bluebottle.wallposts.models import SystemWallpost, TextWallpost


@receiver(post_save, sender=Order)
def _order_status_post_save(sender, instance, **kwargs):
    """
    - Update amount on project when order is in an ending status.
    """

    if instance.status in [StatusDefinition.SUCCESS, StatusDefinition.PENDING,
                           StatusDefinition.PLEDGED, StatusDefinition.FAILED]:

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
                           StatusDefinition.PLEDGED, StatusDefinition.FAILED]:
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

                # Create Wallpost on project wall if there isn't a wallpost for this donation yet
                if TextWallpost.objects.filter(donation=donation).count() == 0:
                    post = SystemWallpost()
                    post.content_object = donation.project
                    post.related_object = donation
                    post.donation = donation
                    post.author = author
                    post.ip = '127.0.0.1'
                    post.save()

                # Create Wallpost on fundraiser wall (if FR present)
                if donation.fundraiser:
                    fr_post = SystemWallpost()
                    fr_post.content_object = donation.fundraiser
                    fr_post.related_object = donation
                    fr_post.donation = donation
                    fr_post.author = author
                    fr_post.ip = '127.0.0.1'
                    fr_post.save()
