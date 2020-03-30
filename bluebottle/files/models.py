import os
import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.files.fields import ImageField


class File(models.Model):

    def get_file_path(self, filename):
        ext = filename.split('.')[-1]
        filename = "%s.%s" % (uuid.uuid4(), ext)
        return os.path.join('files', filename)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateField(_('created'), default=timezone.now)
    file = models.FileField(_('file'), upload_to=get_file_path)
    owner = models.ForeignKey(
        'members.Member',
        verbose_name=_('owner'),
        related_name='own_%(class)s',
    )
    used = models.BooleanField(_('used'), default=False)

    def __unicode__(self):
        return str(self.id)

    class JSONAPIMeta:
        resource_name = 'files'

    class Meta:
        abstract = True


class Image(File):
    class JSONAPIMeta:
        resource_name = 'images'


class Document(File):
    class JSONAPIMeta:
        resource_name = 'documents'


class RelatedImage(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    image = ImageField()
