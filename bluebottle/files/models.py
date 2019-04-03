import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        'members.Member',
        verbose_name=_('owner'),
        related_name='files',
    )

    created = models.DateField(_('created'), default=timezone.now)
    file = models.FileField(_('file'), upload_to='files')
    owner = models.ForeignKey(
        'members.Member',
        verbose_name=_('owner'),
        related_name='own_%(class)s',
    )
    used = models.BooleanField(_('used'), default=False)

    class JSONAPIMeta:
        resource_name = 'files'
