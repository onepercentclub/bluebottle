from django.dispatch import receiver

from bluebottle.common.signals import platform_event
from bluebottle.mails.models import Mail


@receiver(platform_event)
def handle_mail(sender, obj, name, signal, **kwargs):

    for mail in Mail.objects.filter(event=name):
        mail.send()
