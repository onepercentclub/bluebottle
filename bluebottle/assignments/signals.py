from django.db.models.signals import pre_save
from django.dispatch.dispatcher import receiver

from bluebottle.assignments.models import Assignment
from bluebottle.assignments.messages import AssignmentDateChanged


@receiver(pre_save, sender=Assignment)
def send_date_change(sender, instance, *args, **kwargs):
    if instance.pk:
        current = Assignment.objects.get(pk=instance.pk)

        if current.end_date != instance.end_date:
            AssignmentDateChanged(instance).compose_and_send()
