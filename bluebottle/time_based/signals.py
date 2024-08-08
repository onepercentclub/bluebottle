from django.db.models.signals import post_delete
from django.dispatch import receiver

from bluebottle.time_based.models import (
    DeadlineParticipant,
    ScheduleParticipant,
    Registration,
)


@receiver([post_delete], sender=DeadlineParticipant)
@receiver([post_delete], sender=ScheduleParticipant)
def update_delete_registration(sender, instance, **kwargs):

    try:
        if instance.registration.participants.count() == 0:
            instance.registration.delete()
    except Registration.DoesNotExist:
        # Catch the case where the registration is already deleted
        pass
