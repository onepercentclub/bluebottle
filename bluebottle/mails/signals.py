from django.dispatch import receiver
from django.template import engines

from bluebottle.common.signals import platform_event
from bluebottle.mails.models import Mail
from bluebottle.mails.tasks import send_mail


@receiver(platform_event)
def handle_mail(sender, obj, name, signal, **kwargs):

    for mail in Mail.objects.filter(event=name):
        django_engine = engines['django']

        recipients = getattr(obj, obj.recipients)
        for recipient in recipients:
            context = {'obj': obj, 'recipient': recipient}
            subject = django_engine.from_string(mail.subject).render(context=context)
            message = django_engine.from_string(mail.body).render(context=context)
            send_mail(recipient, sender, subject, message, tenant=None, send=False)
