from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from bluebottle.members.models import Member
from bluebottle.activities.models import Activity
from bluebottle.files.fields import ImageField


class Update(models.Model):
    author = models.ForeignKey(
        Member,
        verbose_name=_('Author'),
        null=True,
        on_delete=models.deletion.CASCADE
    )
    activity = models.ForeignKey(
        Activity,
        verbose_name=_('Activity'),
        on_delete=models.deletion.CASCADE,
        related_name='updates'
    )
    parent = models.ForeignKey(
        'self',
        verbose_name=_('Parent'),
        on_delete=models.deletion.CASCADE,
        related_name='replies',
        null=True
    )

    message = models.TextField(_('message'))
    image = ImageField(blank=True, null=True)
    created = models.DateTimeField(_("created"), default=now)

    def save(self, *args, **kwargs):
        if self.parent and self.parent.parent:
            raise ValidationError('Replies can not be nested')

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Update')

    class JSONAPIMeta():
        resource_name = 'updates'
