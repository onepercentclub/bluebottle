from django.db import models
from django.utils.translation import gettext_lazy as _

from bluebottle.members.models import Member


class ActionDismissal(models.Model):
    user = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='action_dismissals')
    action_type = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField(default=0)
    dismissed_at = models.DateTimeField(auto_now=True)
    snoozed_until = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        verbose_name = _('action dismissal')
        verbose_name_plural = _('action dismissals')
        unique_together = ('user', 'action_type', 'object_id')

    def __str__(self):
        return '{}:{} ({})'.format(self.action_type, self.object_id, self.user)
