from django.db import models
from django.utils.translation import gettext_lazy as _

from bluebottle.members.models import Member
from bluebottle.activities.models import Activity


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

    message = models.TextField(_('message'))
