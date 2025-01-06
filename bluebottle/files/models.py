from builtins import str
from builtins import object
import os
import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from future.utils import python_2_unicode_compatible

from bluebottle.files.fields import ImageField
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection


@python_2_unicode_compatible
class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateField(_('created'), default=timezone.now)
    file = models.FileField(
        _('file'),
        upload_to='files',
        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.PRIVATE_FILE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]

    )
    owner = models.ForeignKey(
        'members.Member',
        verbose_name=_('owner'),
        related_name='own_%(class)s',
        on_delete=models.CASCADE
    )
    used = models.BooleanField(_('used'), default=False)
    name = models.CharField(null=True, blank=True, max_length=50)

    def save(self, *args, **kwargs):
        if not self.name and self.file.name:
            self.name = self.file.name[:50]

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.id)

    class JSONAPIMeta(object):
        resource_name = 'files'

    class Meta(object):
        abstract = True


class Image(File):
    cropbox = models.CharField(max_length=40, blank=True)

    class JSONAPIMeta(object):
        resource_name = 'images'


class Document(File):
    class JSONAPIMeta(object):
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

    class JSONAPIMeta(object):
        resource_name = 'private-documents'


class RelatedImage(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    image = ImageField(null=True)
