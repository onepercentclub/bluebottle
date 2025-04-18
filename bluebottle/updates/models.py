from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from bluebottle.activities.models import Activity
from bluebottle.files.fields import ImageField
from bluebottle.fsm.triggers import TriggerMixin
from bluebottle.members.models import Member


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

    contribution = models.ForeignKey(
        'activities.Contributor',
        related_name='updates',
        verbose_name=_('Related contribution'),
        help_text=_('The contribution this update is related to, e.g. the donation'),
        on_delete=models.deletion.CASCADE,
        blank=True,
        null=True
    )

    message = models.TextField(_('message'), blank=True, null=True)
    image = ImageField(blank=True, null=True)
    video_url = models.URLField(max_length=100, blank=True, default='')

    pinned = models.BooleanField(_('Pinned'), default=False)

    created = models.DateTimeField(_("created"), default=now)

    notify = models.BooleanField(_('notify supporters'), default=False)

    @property
    def fake_name(self):
        if self.contribution and getattr(self.contribution, 'name', None):
            return self.contribution.name

    def save(self, *args, **kwargs):
        if self.parent and self.parent.parent:
            raise ValidationError('Replies can not be nested')

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Update')
        ordering = ('created',)

    class JSONAPIMeta():
        resource_name = 'updates'

    def __str__(self):
        if self.author:
            return f'{self.author} - {self.created.strftime("%x %X")}'
        return _('Anonymous - {time}').format(time=self.created.strftime("%x %X"))


class UpdateImage(models.Model):
    image = ImageField(null=True)
    update = models.ForeignKey(
        Update,
        related_name='images',
        on_delete=models.CASCADE
    )

    class JSONAPIMeta():
        resource_name = 'updates/images'
