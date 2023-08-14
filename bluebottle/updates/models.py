from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.triggers import TriggerMixin

from bluebottle.members.models import Member
from bluebottle.activities.models import Activity
from bluebottle.files.fields import ImageField


class Update(TriggerMixin, models.Model):
    author = models.ForeignKey(
        Member,
        verbose_name=_('Author'),
        null=True,
        blank=True,
        on_delete=models.deletion.CASCADE
    )
    activity = models.ForeignKey(
        Activity,
        verbose_name=_('Activity'),
        null=True,
        blank=True,
        on_delete=models.deletion.CASCADE,
        related_name='updates'
    )
    parent = models.ForeignKey(
        'self',
        verbose_name=_('Reply to'),
        on_delete=models.deletion.CASCADE,
        related_name='replies',
        blank=True,
        null=True
    )

    message = models.TextField(_('message'))
    image = ImageField(blank=True, null=True)
    video_url = models.URLField(max_length=100, blank=True, default='')

    pinned = models.BooleanField(_('Pinned'), default=False)

    created = models.DateTimeField(_("created"), default=now)
    notify = models.BooleanField(_('notify supporters'), default=False)

    def save(self, *args, **kwargs):
        if self.parent and self.parent.parent:
            raise ValidationError('Replies can not be nested')

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Update')

    class JSONAPIMeta():
        resource_name = 'updates'


class UpdateImage(models.Model):
    image = ImageField()
    update = models.ForeignKey(
        Update,
        related_name='images',
        on_delete=models.CASCADE
    )
