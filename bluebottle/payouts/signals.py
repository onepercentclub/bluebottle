from .models import ProjectPayout
from bluebottle.journals.models import create_journal_for_sender

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, weak=False, sender=ProjectPayout)
def create_donation_journal_after_donation_is_changed(sender, instance, created, **kwargs):
    create_journal_for_sender(sender=sender, instance=instance, created=created)
