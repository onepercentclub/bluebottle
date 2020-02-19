from django.db.models.signals import pre_save, post_save
from django.dispatch.dispatcher import receiver

from bluebottle.events.models import Event, Participant
from bluebottle.events.messages import EventDateChanged, ParticipantApplicationMessage


@receiver(post_save, sender=Participant)
def send_application_message(sender, instance, created, *args, **kwargs):
    if created:
        ParticipantApplicationMessage(instance).compose_and_send()


@receiver(pre_save, sender=Event)
def send_date_change(sender, instance, *args, **kwargs):
    if instance.pk:
        current = Event.objects.get(pk=instance.pk)

        if current.start != instance.start:
            EventDateChanged(instance).compose_and_send()
