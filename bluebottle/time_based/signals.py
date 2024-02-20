from bluebottle.time_based.models import DeadlineParticipant
from django.db.models.signals import pre_delete
from django.dispatch import receiver


@receiver([pre_delete], sender=DeadlineParticipant)
def update_delete_student(sender, instance, **kwargs):
    if instance.registration.participants.count() == 1:
        instance.registration.delete()
