from bluebottle.bb_donations.signals import donation_status_changed
from django.dispatch import Signal

# This signal indicates that the supplied project has been funded.
#
# :param first_time_funded: Whether or not the project has reached the funded state before. For instance, a project
#                           can become "unfunded" when a donation that was pending fails.
#
from django.dispatch.dispatcher import receiver

project_funded = Signal(providing_args=['first_time_funded'])


@receiver(donation_status_changed)
def _donation_status_changed(sender, donation):
    donation.project.update_amounts()
