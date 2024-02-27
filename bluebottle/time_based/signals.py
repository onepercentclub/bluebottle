from bluebottle.time_based.models import DeadlineParticipant
from django.db.models.signals import post_delete
from django.dispatch import receiver


@receiver([post_delete], sender=DeadlineParticipant)
def update_delete_registration(sender, instance, **kwargs):
    if instance.registration.participants.count() == 0:
        instance.registration.delete()
