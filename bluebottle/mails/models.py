from django.db import models
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatedFields, TranslatableModel

from bluebottle.utils.models import BasePlatformSettings


class MailPlatformSettings(BasePlatformSettings):
    email_logo = models.ImageField(null=True, blank=True, upload_to='site_content/')

    class Meta:
        verbose_name_plural = _('mail platform settings')
        verbose_name = _('mail platform settings')


class Mail(TranslatableModel):

    MAIL_EVENTS = (
        ('member.created', 'Member Created'),
        ('donation.success', 'Donation Success'),
        ('task_member.applied', 'Task Member Applied'),
        ('task_member.accepted', 'Task Member Accepted'),
        ('task_member.rejected', 'Task Member Rejected'),
        ('task_member.withdrew', 'Task Member Withdrew'),
        ('task_member.realized', 'Task Member Realised'),
    )

    @property
    def related_class(self):
        from bluebottle.members.models import Member
        from bluebottle.donations.models import Donation
        from bluebottle.tasks.models import TaskMember, Task

        if self.event.startswith('task_member'):
            return TaskMember
        if self.event.startswith('donation'):
            return Donation
        if self.event.startswith('member'):
            return Member
        if self.event.startswith('task'):
            return Task
        return None

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    event = models.CharField(max_length=200, choices=MAIL_EVENTS)
    recipients = models.CharField(max_length=600, blank=True, null=True)

    translations = TranslatedFields(
        subject=models.CharField(_('Subject'), max_length=300, blank=True, null=True),
        body_html=models.TextField(_('Body html')),
        action_title=models.CharField(_('Action title'), max_length=100, blank=True, null=True),
    )

    action_link = models.CharField(_('Action link'), max_length=100, blank=True, null=True)

    test_object = models.IntegerField(null=True, blank=True)
    test_email = models.EmailField(null=True, blank=True)

    @property
    def test_model(self):
        try:
            return self.related_class.objects.get(id=self.test_object)
        except self.related_class.DoesNotExist:
            return None


from signals import *  # NOQA