from django.dispatch.dispatcher import receiver
from django_fsm.signals import post_transition
from django.contrib.auth.models import AnonymousUser
from bluebottle.bb_donations.donationmail import new_oneoff_donation, successful_donation_fundraiser_mail
from bluebottle.utils.model_dispatcher import get_order_model
from bluebottle.utils.utils import StatusDefinition
from bluebottle.wallposts.models import SystemWallPost

ORDER_MODEL = get_order_model()


@receiver(post_transition, sender=ORDER_MODEL)
def _order_status_changed(sender, instance, **kwargs):
    """
    - Update amount on project when order is in an ending status.
    - Get the status from the Order and Send an Email.
    """

    if instance.status in [StatusDefinition.SUCCESS, StatusDefinition.PENDING, StatusDefinition.FAILED]:
        for donation in instance.donations.all():
            donation.project.update_amounts()


            if not donation.anonymous:
               author = donation.order.user
            else:
                author = None
                
            #Create Wallpost on project wall
            post = SystemWallPost()
            post.content_object = donation.project
            post.related_object = donation
            post.author = author
            post.ip = '127.0.0.1'
            post.save()

            # Create Wallpost on fundraiser wall (if FR present)
            if donation.fundraiser:
                fr_post = SystemWallPost()
                fr_post.content_object = donation.fundraiser
                fr_post.related_object = donation
                fr_post.author = author
                fr_post.ip = '127.0.0.1'
                fr_post.save()
                
        # Send mail if status transitions in ro success/pending for the first time.
        if (kwargs['source'] not in [StatusDefinition.SUCCESS, StatusDefinition.PENDING]
            and  kwargs['target'] in [StatusDefinition.SUCCESS, StatusDefinition.PENDING]):

            for donation in instance.donations.all():
                successful_donation_fundraiser_mail(donation)
                new_oneoff_donation(donation)

