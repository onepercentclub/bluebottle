from django.db import models
from django.utils.translation import ugettext_lazy as _

from bluebottle.utils.models import BasePlatformSettings


class MailPlatformSettings(BasePlatformSettings):
    email_logo = models.ImageField(null=True, blank=True, upload_to='site_content/')

    class Meta:
        verbose_name_plural = _('mail platform settings')
        verbose_name = _('mail platform settings')


class Mail(models.Model):

    MAIL_EVENTS = (
        ('member.created', 'Member Created'),
        ('donation.success', 'Donation Success'),
        ('task_member.applied', 'Task Member Applied'),
        ('task_member.accepted', 'Task Member Accepted'),
        ('task_member.rejected', 'Task Member Rejected'),
        ('task_member.withdrew', 'Task Member Withdrew'),
        ('task_member.realized', 'Task Member Realised'),
    )

    event = models.CharField(max_length=200, choices=MAIL_EVENTS)
    recipients = models.CharField(max_length=600)

    subject = models.CharField(max_length=250)
    body = models.TextField()


from signals import *  # NOQA