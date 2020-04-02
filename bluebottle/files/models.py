import os
import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.files.fields import ImageField


class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateField(_('created'), default=timezone.now)
    file = models.FileField(_('file'), upload_to='files')
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


def get_private_path(self, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    upload_to = os.path.join('files', filename)
    if not upload_to.startswith('private'):
        upload_to = 'private/{}'.format(upload_to)
    return upload_to


class PrivateDocument(File):

    file = models.FileField(_('file'), upload_to=get_private_path)

    class JSONAPIMeta:
        resource_name = 'private-documents'


class RelatedImage(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    image = ImageField()
